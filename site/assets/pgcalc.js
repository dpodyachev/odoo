// Калькулятор odoo.conf + postgresql.conf (по мотивам pgtune, с учётом воркеров Odoo). Тексты — в <script type="application/json" class="pc-data">.
(function () {
  "use strict";
  var root = document.querySelector(".pgcalc");
  if (!root) return;
  var T = JSON.parse(root.querySelector(".pc-data").textContent);
  var f = root.querySelector("form");
  var $ = function (s) { return root.querySelector(s); };
  var MB = 1, GB = 1024;
  var LIGHT = 150, HEAVY = 1024, HEAVY_RATIO = 0.2;          // Odoo docs: 80 % light (~150 MB), 20 % heavy (~1 GB)
  var PER_WORKER = Math.round((1 - HEAVY_RATIO) * LIGHT + HEAVY_RATIO * HEAVY);   // ≈ 325 MB

  function num(name, def) { var v = parseFloat(f.elements[name].value); return isFinite(v) && v > 0 ? v : def; }
  function val(name) { var e = f.elements[name]; return e.type === "checkbox" ? e.checked : e.value; }
  function mem(mb) {                                            // PostgreSQL units
    mb = Math.max(1, Math.floor(mb));
    if (mb >= 1024 && mb % 1024 === 0) return (mb / 1024) + "GB";
    return mb + "MB";
  }
  function round64(x) { return Math.max(64, Math.round(x / 64) * 64); }
  function clamp(x, a, b) { return Math.min(b, Math.max(a, x)); }

  // каждая строка – отдельный span; изменившиеся с прошлого расчёта подсвечиваются
  var prev = {};
  function show(el, lines) {
    var key = el.className, old = prev[key] || [];
    el.textContent = "";
    lines.forEach(function (l, i) {
      var s = document.createElement("span");
      s.textContent = l;
      if (prev[key] && old.indexOf(l) < 0) s.className = "pc-chg";
      el.appendChild(s);
      if (i < lines.length - 1) el.appendChild(document.createTextNode("\n"));
    });
    prev[key] = lines;
  }

  function calc() {
    var ver = parseInt(val("ver"), 10);
    var users = num("users", 20);
    var servers = f.elements.servers ? Math.max(1, Math.round(num("servers", 1))) : 1;   // Odoo application servers behind a load balancer
    var usersPer = Math.ceil(users / servers);
    var same = val("layout") === "same";
    var ocpu = Math.round(num("ocpu", 4));
    var oram = num("oram", 8) * GB;
    var dcpu = same ? ocpu : Math.round(num("dcpu", 4));
    var dram = same ? 0 : num("dram", 8) * GB;
    var ssd = val("disk") === "ssd";
    var pgv = parseInt(val("pgv"), 10);
    var replica = val("replica") && ver >= 18;
    var notes = [];
    function ipv(n, d) { var e = f.elements[n]; return e && e.value.trim() ? e.value.trim() : d; }
    var ipO = ipv("ip_odoo", "10.0.0.5"), ipP = ipv("ip_primary", "10.0.0.10"), ipR = ipv("ip_replica", "10.0.0.11");
    var repPage = !!$(".pc-rep");

    // ---- Odoo ----
    var cpuOdoo = same ? Math.max(1, ocpu - Math.ceil(ocpu / 4)) : ocpu;      // shared host: ~25 % CPU for PostgreSQL
    var maxByCpu = cpuOdoo * 2 + 1;
    var workers = clamp(Math.ceil(usersPer / 6) + 1, 2, maxByCpu);           // ~6 concurrent users per worker
    if (Math.ceil(usersPer / 6) + 1 > maxByCpu) {
      var need = Math.ceil(users / (maxByCpu * 6));
      notes.push(T.n_cpu.replace("{n}", maxByCpu * 6 * servers) + " " + T.n_servers.replace("{s}", need));
    }
    var osRes = Math.round(1024 + 0.05 * oram);
    var pgRam, odooRam;
    function odooNeed(w) { return w * PER_WORKER + 400; }                     // + cron threads, gevent, main process
    if (same) {
      while (workers > 2 && oram - osRes - odooNeed(workers) < oram * 0.25) workers--;
      odooRam = odooNeed(workers);
      pgRam = Math.max(512, Math.min(oram - osRes - odooRam, oram * 0.5));   // rest for PostgreSQL, but max. half – Odoo needs headroom for peaks
      if (pgRam < oram * 0.25) notes.push(T.n_ram);
    } else {
      while (workers > 2 && odooNeed(workers) > oram - osRes) workers--;
      odooRam = oram - osRes;
      pgRam = dram;                                                          // dedicated DB host: pgtune-style, whole RAM
      if (odooNeed(workers) > oram - osRes) notes.push(T.n_ram);
    }
    var cron = workers >= 6 ? 2 : 1;
    // limits are ceilings for peaks (big reports/imports), not the average: what is left after OS (and shared_buffers) per worker × 1.5
    var avail = same ? oram - osRes - pgRam / 4 : oram - osRes;
    var soft = round64(clamp(avail / workers * 1.5, 640, 2048));
    var hard = round64(Math.min(soft * 1.25, 2560));
    var procs = workers + cron + 1;                                          // HTTP workers + cron + gevent
    var dbMaxconn = procs > 9 ? 16 : 32;
    var maxConn = Math.max(100, Math.ceil((procs * servers * 3 + 20) / 10) * 10);
    if (servers > 1) notes.push(T.n_multi.replace("{s}", servers));
    if (maxConn > 500) notes.push(T.n_pool.replace("{m}", maxConn));
    if (workers * servers > dcpu * 6) notes.push(T.n_dbcpu.replace("{w}", workers * servers).replace("{c}", dcpu));

    var oc = [
      "[options]",
      "; Odoo " + ver + " · " + T.c_gen,
      servers > 1 ? "; " + T.c_servers.replace("{s}", servers) : null,
      "workers = " + workers + "                 ; ≈ " + (workers * 6) + " " + T.c_users,
      "max_cron_threads = " + cron,
      "limit_memory_soft = " + (soft * 1024 * 1024) + "   ; " + soft + " MB",
      "limit_memory_hard = " + (hard * 1024 * 1024) + "   ; " + hard + " MB",
      "limit_time_cpu = 600",
      "limit_time_real = 1200",
      "limit_request = 65536",
      "db_maxconn = " + dbMaxconn + "              ; " + T.c_maxconn,
      same ? "db_host = False             ; " + T.c_socket : "db_host = " + ipP + "         ; " + T.c_dbhost,
      "db_port = 5432",
    ];
    if (replica) oc.push("db_replica_host = " + ipR + "  ; " + T.c_replica, "db_replica_port = 5432");
    oc.push("proxy_mode = True", "gevent_port = 8072", "list_db = False", "; admin_passwd = <" + T.c_secret + ">",
            "; db_user / db_password = <" + T.c_secret + ">");

    // ---- PostgreSQL ----
    var sb = round64(pgRam / 4);
    var ecs = round64(pgRam * 3 / 4);
    var mwm = round64(Math.min(pgRam / 16, 2 * GB));
    var wb = sb * 0.03; wb = wb >= 14 ? 16 : Math.max(1, Math.floor(wb));
    var par = dcpu >= 4;
    var gather = par ? Math.min(4, Math.ceil(dcpu / 2)) : 1;
    var wm = Math.max(4, (pgRam - sb) / ((maxConn + dcpu) * 3) / gather);
    var p = [
      ["max_connections", maxConn, T.c_conn.replace("{p}", procs * servers)],
      ["shared_buffers", mem(sb), "25 % RAM"],
      ["effective_cache_size", mem(ecs), "75 % RAM"],
      ["maintenance_work_mem", mem(mwm), ""],
      ["work_mem", mem(wm), T.c_workmem],
      ["checkpoint_completion_target", "0.9", ""],
      ["wal_buffers", mem(wb), ""],
      ["min_wal_size", "1GB", ""],
      ["max_wal_size", "4GB", ""],
      ["default_statistics_target", "100", ""],
      ["random_page_cost", ssd ? "1.1" : "4", ssd ? "SSD/NVMe" : "HDD"],
      ["effective_io_concurrency", ssd ? "200" : "2", ""],
    ];
    if (pgRam >= 32 * GB) p.push(["huge_pages", "try", ""]);
    if (par) p.push(["max_worker_processes", dcpu, ""], ["max_parallel_workers_per_gather", gather, ""],
                    ["max_parallel_workers", dcpu, ""], ["max_parallel_maintenance_workers", gather, ""]);
    p.push(["", "", "Odoo"],
           ["jit", "off", T.c_jit],
           ["shared_preload_libraries", "'pg_stat_statements'", T.c_restart],
           ["track_io_timing", "on", ""],
           ["log_min_duration_statement", "2000", T.c_slow],
           ["autovacuum_vacuum_scale_factor", "0.05", T.c_av],
           ["autovacuum_analyze_scale_factor", "0.02", ""],
           ["listen_addresses", same ? "'localhost'" : "'*'", same ? "" : T.c_hba]);
    var common = p.slice();                                   // memory/planner/Odoo part – same on the replica
    if (replica) p.push(["", "", T.c_repl_h], ["wal_level", "replica", ""], ["max_wal_senders", "10", ""]);
    if (replica && !repPage) p.push(["hot_standby_feedback", "on", T.c_repl_only]);
    var fmt = val("fmt");
    function render(list, head) {
      var out = [head];
      list.forEach(function (r) {
        if (!r[0]) { out.push("", "# --- " + r[2]); return; }
        var v = String(r[1]);
        if (fmt === "alter") {
          var q = /^'.*'$/.test(v) ? v : "'" + v + "'";
          out.push("ALTER SYSTEM SET " + r[0] + " = " + q + ";" + (r[2] ? "  -- " + r[2] : ""));
        } else {
          out.push(r[0] + " = " + v + (r[2] ? "    # " + r[2] : ""));
        }
      });
      if (fmt === "alter") out.push("", "SELECT pg_reload_conf();  -- " + T.c_restart2);
      return out;
    }
    var pc = render(p, "# PostgreSQL " + pgv + " · " + (same ? T.c_same : T.c_dedicated) + (repPage ? " · primary " + ipP : "")
                       + " · RAM " + mem(pgRam) + ", CPU " + dcpu);
    if (repPage) {
      var rl = common.concat([["", "", "hot standby"], ["hot_standby", "on", ""], ["hot_standby_feedback", "on", "fewer 'conflict with recovery' cancellations"],
                              ["max_standby_streaming_delay", "30s", ""], ["wal_level", "replica", "same as primary"]]);
      show($(".pc-rep"), render(rl, "# PostgreSQL " + pgv + " · replica " + ipR + " · RAM " + mem(pgRam) + ", CPU " + dcpu));
      show($(".pc-setup"), [
        "# pg_hba.conf on the PRIMARY " + ipP,
        "host  all          odoo        " + ipO + "/32  scram-sha-256",
        "host  replication  replicator  " + ipR + "/32  scram-sha-256",
        "",
        "# pg_hba.conf on the REPLICA " + ipR + " (read-only connections from Odoo)",
        "host  all          odoo        " + ipO + "/32  scram-sha-256",
        "",
        "# 1) primary: replication role (password into ~/.pgpass on the replica, not into scripts)",
        "sudo -u postgres psql -c \"CREATE ROLE replicator WITH REPLICATION LOGIN\" -c '\\password replicator'",
        "sudo systemctl reload postgresql",
        "",
        "# 2) replica: empty data directory, copy from the primary, -R writes primary_conninfo + standby.signal",
        "sudo systemctl stop postgresql",
        "sudo -u postgres bash -c 'rm -rf /var/lib/postgresql/" + pgv + "/main/*'",
        "sudo -u postgres pg_basebackup -h " + ipP + " -U replicator -D /var/lib/postgresql/" + pgv + "/main -R -X stream -P",
        "sudo systemctl start postgresql",
        "",
        "# 3) check",
        "psql -h " + ipP + " -U odoo -d postgres -c \"SELECT client_addr, state, sync_state, replay_lag FROM pg_stat_replication;\"",
        "psql -h " + ipR + " -U odoo -d postgres -c \"SELECT pg_is_in_recovery(), now() - pg_last_xact_replay_timestamp() AS lag;\"",
        "",
        "# 4) odoo.conf: db_replica_host = " + ipR + " (above), restart Odoo, watch the log for",
        "#    'retrying with a read/write cursor' and 'Failed to open a readonly cursor'",
      ]);
    }

    show($(".pc-odoo"), oc.filter(function (l) { return l !== null; }));
    show($(".pc-pg"), pc);
    root.querySelectorAll("output[data-for]").forEach(function (o) {
      o.textContent = f.elements[o.getAttribute("data-for")].value;
    });

    // RAM bar (Odoo host)
    var total = oram;
    var parts = same ? [["os", osRes], ["odoo", odooRam], ["pg", pgRam]] : [["os", osRes], ["odoo", oram - osRes]];
    $(".pc-bar").innerHTML = "";
    parts.forEach(function (x) {
      var s = document.createElement("span");
      s.className = "pcb-" + x[0];
      s.style.width = (100 * x[1] / total).toFixed(1) + "%";
      s.textContent = T["b_" + x[0]] + " " + (x[1] / 1024).toFixed(1) + " GB";
      s.title = s.textContent;
      $(".pc-bar").appendChild(s);
    });
    $(".pc-sum").textContent = (servers > 1 ? servers + " × " : "") + T.s_sum.replace("{w}", workers).replace("{u}", workers * 6 * servers)
      .replace("{c}", procs * 2 * servers).replace("{m}", maxConn);
    var nl = $(".pc-notes"); nl.innerHTML = "";
    notes.forEach(function (n) { var li = document.createElement("li"); li.textContent = n; nl.appendChild(li); });
    nl.hidden = !notes.length;
    $(".pc-dbhost").hidden = same;
    if ($(".pc-replica")) $(".pc-replica").hidden = ver < 18;
  }

  f.addEventListener("input", calc);
  f.addEventListener("change", calc);
  f.addEventListener("submit", function (e) { e.preventDefault(); });
  root.querySelectorAll(".pc-copy").forEach(function (b) {
    b.addEventListener("click", function () {
      var txt = $(b.getAttribute("data-t")).textContent;
      if (!navigator.clipboard) return;
      navigator.clipboard.writeText(txt).then(function () {
        var o = b.textContent; b.textContent = T.copied; setTimeout(function () { b.textContent = o; }, 1500);
      }, function () {});
    });
  });
  calc();
})();
