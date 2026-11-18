# Статья 28: как измерить и сравнить производительность VPS под Ubuntu – диск (dd, fio, hdparm, ioping, badblocks),
# CPU, память, steal time, сеть (mtr, ping, iperf3). Повод: два одинаковых VPS у одного провайдера, один медленный
# и с потерями пакетов. Команды и примеры вывода проверены на нашем KVM VPS (AMD EPYC, 4 vCPU, SSD), 2026-11-18,
# fio 3.39, sysbench 1.0.20. Все 6 языков.

VPSBENCH = {
    "slug": "vps-performance-benchmark-ubuntu-disk-cpu-memory-network",
    "date": "2026-11-18",
    "tags": ["Linux", "VPS", "Performance", "Ubuntu"],
    "code": {
        "install": ("bash · Ubuntu 22.04 / 24.04: install the tools (fio, sysbench … come from universe)",
                    """sudo apt update
sudo apt install -y fio sysbench ioping mtr-tiny iperf3 hdparm sysstat"""),
        "inventory": ("bash · first: are the two servers really identical?", """lscpu | grep -E 'Model name|^CPU\\(s\\)|Hypervisor'   # the CPU model can differ between host nodes
nproc; free -h; uname -r
lsblk -o NAME,SIZE,ROTA,TYPE,MOUNTPOINT                  # ROTA 0 = SSD/NVMe (as the guest sees it)
systemd-detect-virt; df -hT /"""),
        "steal": ("bash · steal time: is somebody else using \"our\" CPU? (our VPS, idle)", """vmstat 1 10        # st = steal, wa = waiting for the disk, si/so = swap in/out
procs -----------memory---------- ---swap-- -----io---- -system-- -------cpu-------
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st gu
 0  0      0 1387536  68484 3687648    0    0     0     8  804 1227  2  0 98  0  0  0
 0  0      0 1387036  68484 3687648    0    0     0     0  775 1275  1  0 98  0  0  0

mpstat -P ALL 1 5  # %steal per vCPU (package sysstat)
top                # header line "%Cpu(s): ... 0.0 st\""""),
        "dd": ("bash · dd: sequential write and read past the page cache (our VPS)", """dd if=/dev/zero of=./dd.test bs=1M count=1024 oflag=direct     # write
1073741824 bytes (1.1 GB, 1.0 GiB) copied, 0.825121 s, 1.3 GB/s
dd if=./dd.test of=/dev/null bs=1M iflag=direct                 # read
1073741824 bytes (1.1 GB, 1.0 GiB) copied, 0.874313 s, 1.2 GB/s
rm ./dd.test
# instead of oflag=direct: conv=fdatasync (waits until the data is on disk)
# without direct / fdatasync, dd measures RAM (page cache), not the disk"""),
        "fio": ("bash · fio: random 4k read/write – what a database really does (our VPS)", """fio --name=rand4k --filename=./fio.test --size=1G --rw=randrw --rwmixread=70 --bs=4k \\
    --iodepth=32 --ioengine=libaio --direct=1 --runtime=30 --time_based --group_reporting
  read: IOPS=26.7k, BW=104MiB/s (109MB/s)
    clat percentiles (usec):
     | 99.00th=[ 1926], 99.50th=[ 2180], 99.90th=[ 4424], 99.95th=[ 5866],
  write: IOPS=11.4k, BW=44.7MiB/s (46.9MB/s)
rm ./fio.test

# sequential 1M read – backups, restore, large files
fio --name=seq --filename=./fio.test --size=1G --rw=read --bs=1M --iodepth=16 \\
    --ioengine=libaio --direct=1 --runtime=15 --time_based
  read: IOPS=2143, BW=2144MiB/s (2248MB/s)
rm ./fio.test"""),
        "fsync": ("bash · fio: small writes, each with fdatasync – like PostgreSQL on COMMIT (our VPS)", """fio --name=fsync --directory=. --rw=write --bs=8k --size=128M --ioengine=sync \\
    --fdatasync=1 --runtime=20 --time_based
  write: IOPS=1331, BW=10.4MiB/s
    sync (usec): min=203, max=34440, avg=731.91
     | 99.00th=[ 2073], 99.50th=[ 2540], 99.90th=[ 5735], 99.95th=[11469],
rm -f ./fsync.*"""),
        "hdparm": ("bash · hdparm, ioping, badblocks (device name from lsblk: vda, sda, nvme0n1 …)", """sudo hdparm -Tt /dev/vda       # -T = cache/RAM, -t = buffered sequential read for ~3 s
ioping -c 10 .                 # latency of single 4k requests – "ping for the disk"
  min/avg/max/mdev = 441.8 us / 542.4 us / 625.1 us / 62.1 us
sudo badblocks -sv /dev/vda    # read-only scan of the WHOLE disk – hours on a large disk
# NEVER badblocks -w on a disk with data: write mode overwrites everything"""),
        "cpu": ("bash · CPU: one thread and all threads (our VPS: AMD EPYC, 4 vCPU)", """sysbench cpu --threads=1 --time=10 run | grep 'events per second'
    events per second:  3590.23
sysbench cpu --threads=$(nproc) --time=10 run | grep 'events per second'
    events per second: 14129.86     # ~4x one thread = the 4 vCPU really run in parallel
openssl speed -seconds 3 sha256 | tail -1     # a second opinion without extra packages
sha256  83511.87k  275571.90k  710602.75k  1212295.85k  1490460.67k  1525175.64k"""),
        "mem": ("bash · memory bandwidth (our VPS)", """sysbench memory --memory-block-size=1M --memory-total-size=20G run | grep transferred
20480.00 MiB transferred (23756.37 MiB/sec)
sysbench memory --memory-block-size=1M --memory-total-size=20G --memory-oper=read run | grep transferred"""),
        "net": ("bash · network: loss and latency – in both directions", """mtr -rwbzc 200 1.1.1.1      # report, wide, names+IPs, AS numbers, 200 packets
HOST: vps                                         Loss%   Snt   Last   Avg  Best  Wrst StDev
  4. AS???    ???                                 100.0   100    0.0   0.0   0.0   0.0   0.0   # router does not answer ICMP
  8. AS24940  juniper4.dc1.hel1.hetzner.com         0.0%   100    0.5   3.0   0.5  34.4   6.3   # spikes: ICMP is low priority there
 11. AS13335  one.one.one.one (1.1.1.1)             0.0%   100    1.4   1.5   1.3   4.2   0.6   # last hop clean = path is fine

mtr -rwbzc 200 <server-ip>            # the same from your office/home towards the server
mtr -rwbzc 200 -T -P 443 <server-ip>  # TCP instead of ICMP, if ICMP is filtered
ping -c 500 -i 0.2 -q <server-ip>     # summary: packet loss, rtt min/avg/max/mdev
ip -s link show eth0                  # RX/TX errors and dropped on the server's interface
nstat -az | grep -iE 'retrans|drop'   # TCP retransmits
iperf3 -s                             # on server A
iperf3 -c <A> -t 30; iperf3 -c <A> -t 30 -R   # on server B: upload, then download (-R)"""),
        "script": ("bash · bench.sh – the same set on every server, result in a file", """#!/bin/bash
# bench.sh – run in a directory with ~2 GB free space; result: bench-<host>-<date>.txt
OUT="bench-$(hostname)-$(date +%F-%H%M).txt"
{
echo "### $(date -Is) $(hostname)"
lscpu | grep -E 'Model name|^CPU\\(s\\)'; free -h | head -2; uname -r
echo "### steal: vmstat 1 10"; vmstat 1 10
echo "### cpu"; for t in 1 "$(nproc)"; do echo "threads=$t"; sysbench cpu --threads="$t" --time=10 run | grep 'events per second'; done
echo "### memory"; sysbench memory --memory-block-size=1M --memory-total-size=20G run | grep transferred
echo "### dd write/read"
dd if=/dev/zero of=./dd.test bs=1M count=1024 oflag=direct 2>&1 | tail -1
dd if=./dd.test of=/dev/null bs=1M iflag=direct 2>&1 | tail -1; rm -f ./dd.test
echo "### fio 4k randrw"
fio --name=rand4k --filename=./fio.test --size=1G --rw=randrw --rwmixread=70 --bs=4k --iodepth=32 \\
    --ioengine=libaio --direct=1 --runtime=30 --time_based --group_reporting | grep -E 'IOPS=|99.00th'
rm -f ./fio.test
echo "### fio fdatasync"
fio --name=fsync --directory=. --rw=write --bs=8k --size=128M --ioengine=sync --fdatasync=1 \\
    --runtime=20 --time_based | grep -E 'IOPS=| sync \\(usec\\)'
rm -f ./fsync.*
echo "### mtr"; mtr -rwbzc 100 1.1.1.1
} 2>&1 | tee "$OUT\""""),
    },
    "links": [
        ("Blog: PostgreSQL load test (pgbench) and a read replica", "@blog:postgresql-load-test-pgload-replica"),
        ("Blog: how many users can one Odoo server handle", "@blog:odoo-how-many-users-one-server-workers"),
        ("Blog: Odoo after a year in production – monitoring", "@blog:odoo-production-hardening-housekeeping-monitoring"),
        ("fio documentation", "https://fio.readthedocs.io/en/latest/fio_doc.html"),
        ("sysbench", "https://github.com/akopytov/sysbench"),
        ("mtr", "https://github.com/traviscross/mtr"),
    ],
    "t": {},
}


def _d(title, summary, intro, note, h, case_p, rules_ul, steal_p, steal_ul, disk_p, disk_ul, cpu_ul, net_ul,
       script_p, table, prov_ul, closing, links):
    return {"title": title, "summary": summary, "body": [
        ("p", intro), ("note", note),
        ("h", h[0]), ("p", case_p),
        ("h", h[1]), ("ul", rules_ul), ("code", "install"), ("code", "inventory"),
        ("h", h[2]), ("p", steal_p), ("code", "steal"), ("ul", steal_ul),
        ("h", h[3]), ("p", disk_p), ("code", "dd"), ("code", "fio"), ("code", "fsync"), ("code", "hdparm"), ("ul", disk_ul),
        ("h", h[4]), ("code", "cpu"), ("code", "mem"), ("ul", cpu_ul),
        ("h", h[5]), ("code", "net"), ("ul", net_ul),
        ("h", h[6]), ("p", script_p), ("code", "script"), ("table", table),
        ("h", h[7]), ("ul", prov_ul),
        ("h", h[8]), ("p", closing),
        ("links", links)]}


VPSBENCH["t"]["en"] = _d(
    "Two identical VPS, one is slow: how to measure disk, CPU, memory and network on Ubuntu",
    "We ordered two VPS with the same plan from one provider – one was noticeably slower and lost packets. How to prove it with numbers: dd, fio, hdparm, ioping and badblocks for the disk, sysbench and openssl for CPU and memory, steal time, mtr, ping and iperf3 for the network, a ready script and what to send to the provider.",
    "Two servers with the same plan, the same image, ordered on the same day at Contabo. One worked normally, the other was slow in everything – and `mtr` showed lost packets. \"Feels slow\" is not something support can work with. You need numbers from both servers, measured the same way at the same time. This article is the set of measurements we use for that.",
    "All commands work on Ubuntu 22.04 / 24.04 (and Debian). The example outputs come from our own KVM VPS (AMD EPYC, 4 vCPU, SSD) – they show the format, they are not a reference value. The tests write 1–2 GB of files: do not run them on a production server at peak time.",
    ["The case", "Rules for a fair comparison", "Steal time – the first thing to check", "Disk: read and write", "CPU and memory", "Network: loss and latency", "Everything in one script", "What to send to the provider", "Conclusion"],
    "On a VPS you share a physical host with other customers. The plan guarantees vCPU, RAM and disk size, but not how busy the host node is, how fast its storage is right now or how loaded its network uplink is. Two \"identical\" VPS can land on different nodes – with a different CPU generation, different storage and different neighbours. That is exactly what we have to show.",
    ["**Same commands, same versions** of fio and sysbench on both servers – numbers from different versions are not comparable.",
     "**At the same time, and repeated**: 3 runs at different hours (morning, evening). A noisy neighbour comes and goes; one run proves nothing.",
     "**Idle servers**: no backups, updates or cron jobs running during the test (check with `top`). Otherwise you measure yourself.",
     "**Check the inventory first**: CPU model, vCPU count, RAM, kernel and disk type – sometimes the \"same\" plan is simply a different CPU."],
    "Steal time is the share of time in which our vCPU wanted to run but the hypervisor gave the physical core to somebody else. It is the most direct sign of an overloaded host node, and it costs nothing to measure.",
    ["`st` around 0 – fine. Regularly 5–10 % and more under load – the host is overbooked; your CPU numbers will jump from run to run.",
     "`wa` high while the disk is busy – the process waits for storage; look at the disk tests.",
     "`si`/`so` not 0 – the server swaps; then every test is wrong. Fix memory first."],
    "For a server with a database (Odoo, PostgreSQL), the most important number is not MB/s of a large file, but how many small random operations per second the disk does and how long the slowest of them take. That is why there are several tools:",
    ["**dd** – simple, available everywhere, but only sequential. Always with `oflag=direct`/`iflag=direct` or `conv=fdatasync`, otherwise you measure RAM. Storage that compresses or deduplicates can make `/dev/zero` look faster than real data.",
     "**fio** – the main tool. `randrw 4k` with `iodepth=32` shows IOPS and the **99th percentile latency** (`99.00th`, in µs). Two servers can have similar average IOPS while one has p99 in the tens of milliseconds – that is the one users feel as \"Odoo hangs\".",
     "**fio with fdatasync** – each write waits for the disk to confirm it, just like PostgreSQL on COMMIT. Network storage that is fast on paper often drops here.",
     "**hdparm -Tt** – a quick look; on a virtual disk `-t` measures the provider's storage path and cache, so use it only to compare the two servers, not as an absolute value.",
     "**ioping** – latency of single requests, good to watch over a few minutes: a healthy disk has a stable `mdev`.",
     "**badblocks** – checks for bad sectors on a physical disk. On a VPS it reads the whole virtual disk for hours and finds nothing the provider would not see themselves; we do not use it there. And never `-w` on a disk with data."],
    ["**sysbench cpu** with one thread shows the speed of one core, with all threads – whether the vCPU really run in parallel. All threads should give roughly \"one thread × vCPU\". Much less means shared cores that are busy.",
     "**openssl speed** – a second opinion without installing anything; compare the last column.",
     "**sysbench memory** – memory bandwidth; differences of several times between \"identical\" servers mean a different host or a heavily loaded one.",
     "Odoo workers run Python in one thread each – the single-thread number matters more for page response than the total."],
    ["**Loss only at an intermediate hop is not loss.** Routers answer ICMP with low priority or not at all (`???`, 100 %). What matters is the **last hop**: if it is clean, the path is fine.",
     "**Real loss** starts at some hop and continues to the end, growing. If it starts at the first hops of the provider – the provider's network or the host node.",
     "**Both directions**: the route back can be different. Run `mtr` from the server outwards and from your office to the server, at least 200 packets.",
     "**On the server itself**: `ip -s link` shows errors and drops on the interface, `nstat` TCP retransmits – if those grow on one server and not on the other, it is not the internet.",
     "**iperf3** between the two servers shows the real bandwidth; run it in both directions (`-R`)."],
    "So that the comparison is honest, we run the same script on both servers, three times, and keep the files. On our VPS two runs in a row differed by about 2 % – a difference of 30–50 % or more between \"identical\" servers is no longer measurement noise.",
    [["What", "Tool", "Compare", "Red flag"],
     ["Steal time", "vmstat, mpstat, top", "`st` under load", "regularly above 5–10 %"],
     ["CPU", "sysbench cpu, openssl speed", "events/s for 1 and all threads", "big gap to the twin; all threads ≪ one thread × vCPU"],
     ["Memory", "sysbench memory", "MiB/s", "several times lower than the twin"],
     ["Disk, random", "fio 4k randrw", "IOPS and `99.00th`", "IOPS several times lower; p99 in tens of ms"],
     ["Disk, sync", "fio fdatasync", "IOPS, sync latency", "far below the twin – PostgreSQL commits will be slow"],
     ["Disk, sequential", "dd, fio 1M, hdparm -t", "MB/s", "much lower than the twin"],
     ["Network", "mtr, ping, iperf3, ip -s link", "loss at the last hop, RTT, Mbit/s, drops", "loss to the final hop, growing drops/retransmits"]],
    ["**Raw output from both servers** (the `bench-*.txt` files), the time of each run and the server IDs – not \"server 2 is slow\".",
     "**mtr in both directions** with 200+ packets and the time; for loss, also `ping -c 500` to the server.",
     "**A concrete request**: check the host node of the slow server, or move the VPS to another node. Mention that the twin with the same plan is several times faster – that is hard to argue with.",
     "**Plan type**: Contabo, like many providers, sells VPS with shared vCPUs and separate products with dedicated cores (Contabo calls them VDS). On shared cores some variation is normal; a factor of several is not.",
     "**Measure every new server right after ordering**, before installing anything: you get a baseline, and if the result is bad you can still cancel or ask for another node before production data is on it."],
    "The same plan does not mean the same server. One script, run on both servers at the same time and repeated, turns \"it feels slow\" into numbers that support can act on. For Odoo and PostgreSQL the numbers to watch are steal time, fio 4k p99 latency and fdatasync IOPS. We run these checks for every server we set up for Odoo – for companies in Germany, Austria and Switzerland.",
    "Links")

VPSBENCH["t"]["de"] = _d(
    "Zwei gleiche VPS, einer ist langsam: Festplatte, CPU, Speicher und Netzwerk unter Ubuntu messen",
    "Wir haben zwei VPS mit demselben Tarif beim selben Anbieter bestellt – einer war deutlich langsamer und verlor Pakete. Wie man das mit Zahlen belegt: dd, fio, hdparm, ioping und badblocks für die Festplatte, sysbench und openssl für CPU und Speicher, Steal Time, mtr, ping und iperf3 für das Netzwerk, ein fertiges Skript und was man dem Anbieter schickt.",
    "Zwei Server mit demselben Tarif, demselben Image, am selben Tag bei Contabo bestellt. Einer lief normal, der andere war in allem langsam – und `mtr` zeigte verlorene Pakete. „Fühlt sich langsam an“ hilft dem Support nicht. Man braucht Zahlen von beiden Servern, gleich gemessen, zur gleichen Zeit. Dieser Artikel ist das Set an Messungen, das wir dafür nutzen.",
    "Alle Befehle funktionieren unter Ubuntu 22.04 / 24.04 (und Debian). Die Beispielausgaben stammen von unserem eigenen KVM-VPS (AMD EPYC, 4 vCPU, SSD) – sie zeigen das Format, sie sind kein Referenzwert. Die Tests schreiben 1–2 GB an Dateien: nicht zur Spitzenzeit auf einem Produktivserver ausführen.",
    ["Der Fall", "Regeln für einen fairen Vergleich", "Steal Time – das Erste, was man prüft", "Festplatte: Lesen und Schreiben", "CPU und Speicher", "Netzwerk: Verluste und Latenz", "Alles in einem Skript", "Was man dem Anbieter schickt", "Fazit"],
    "Auf einem VPS teilt man einen physischen Host mit anderen Kunden. Der Tarif garantiert vCPU, RAM und Plattengröße, aber nicht, wie ausgelastet der Host-Knoten ist, wie schnell sein Speicher gerade ist oder wie voll sein Netzwerk-Uplink. Zwei „gleiche“ VPS können auf verschiedenen Knoten landen – mit anderer CPU-Generation, anderem Speicher und anderen Nachbarn. Genau das muss man zeigen.",
    ["**Gleiche Befehle, gleiche Versionen** von fio und sysbench auf beiden Servern – Zahlen aus verschiedenen Versionen sind nicht vergleichbar.",
     "**Zur gleichen Zeit und wiederholt**: 3 Durchläufe zu verschiedenen Uhrzeiten (morgens, abends). Ein lauter Nachbar kommt und geht; ein Durchlauf beweist nichts.",
     "**Leerlaufende Server**: keine Backups, Updates oder Cron-Jobs während des Tests (mit `top` prüfen). Sonst misst man sich selbst.",
     "**Zuerst die Ausstattung prüfen**: CPU-Modell, Anzahl vCPU, RAM, Kernel und Plattentyp – manchmal ist der „gleiche“ Tarif einfach eine andere CPU."],
    "Steal Time ist der Anteil der Zeit, in dem unsere vCPU laufen wollte, der Hypervisor den physischen Kern aber jemand anderem gab. Es ist das direkteste Zeichen eines überlasteten Host-Knotens, und die Messung kostet nichts.",
    ["`st` um 0 – in Ordnung. Unter Last regelmäßig 5–10 % und mehr – der Host ist überbucht; die CPU-Werte springen von Lauf zu Lauf.",
     "`wa` hoch, während die Platte arbeitet – der Prozess wartet auf den Speicher; siehe Plattentests.",
     "`si`/`so` nicht 0 – der Server swappt; dann ist jeder Test falsch. Zuerst den Speicher klären."],
    "Für einen Server mit Datenbank (Odoo, PostgreSQL) ist die wichtigste Zahl nicht MB/s einer großen Datei, sondern wie viele kleine zufällige Operationen pro Sekunde die Platte schafft und wie lange die langsamsten dauern. Deshalb gibt es mehrere Werkzeuge:",
    ["**dd** – einfach, überall vorhanden, aber nur sequenziell. Immer mit `oflag=direct`/`iflag=direct` oder `conv=fdatasync`, sonst misst man RAM. Speicher, der komprimiert oder dedupliziert, kann `/dev/zero` schneller aussehen lassen als echte Daten.",
     "**fio** – das Hauptwerkzeug. `randrw 4k` mit `iodepth=32` zeigt IOPS und die **Latenz des 99. Perzentils** (`99.00th`, in µs). Zwei Server können ähnliche mittlere IOPS haben, während einer ein p99 im zweistelligen Millisekundenbereich hat – genau das spüren Anwender als „Odoo hängt“.",
     "**fio mit fdatasync** – jeder Schreibvorgang wartet auf die Bestätigung der Platte, genau wie PostgreSQL beim COMMIT. Netzwerkspeicher, der auf dem Papier schnell ist, bricht hier oft ein.",
     "**hdparm -Tt** – ein schneller Blick; auf einer virtuellen Platte misst `-t` den Speicherpfad und Cache des Anbieters, also nur zum Vergleich der beiden Server nutzen, nicht als absoluten Wert.",
     "**ioping** – Latenz einzelner Anfragen, gut über ein paar Minuten zu beobachten: eine gesunde Platte hat ein stabiles `mdev`.",
     "**badblocks** – sucht defekte Sektoren auf einer physischen Platte. Auf einem VPS liest es stundenlang die ganze virtuelle Platte und findet nichts, was der Anbieter nicht selbst sähe; wir nutzen es dort nicht. Und niemals `-w` auf einer Platte mit Daten."],
    ["**sysbench cpu** mit einem Thread zeigt die Geschwindigkeit eines Kerns, mit allen Threads – ob die vCPU wirklich parallel laufen. Alle Threads sollten ungefähr „ein Thread × vCPU“ ergeben. Deutlich weniger heißt: geteilte Kerne, die belegt sind.",
     "**openssl speed** – eine zweite Meinung ohne Installation; die letzte Spalte vergleichen.",
     "**sysbench memory** – Speicherbandbreite; ein Unterschied um ein Mehrfaches zwischen „gleichen“ Servern bedeutet einen anderen oder stark belasteten Host.",
     "Odoo-Worker führen Python jeweils in einem Thread aus – für die Antwortzeit einer Seite zählt der Ein-Thread-Wert mehr als die Summe."],
    ["**Verlust nur an einem Zwischenhop ist kein Verlust.** Router beantworten ICMP mit niedriger Priorität oder gar nicht (`???`, 100 %). Entscheidend ist der **letzte Hop**: ist er sauber, ist der Weg in Ordnung.",
     "**Echter Verlust** beginnt an einem Hop und setzt sich bis zum Ende fort, zunehmend. Beginnt er an den ersten Hops des Anbieters – Netzwerk des Anbieters oder Host-Knoten.",
     "**Beide Richtungen**: der Rückweg kann anders sein. `mtr` vom Server nach außen und vom Büro zum Server ausführen, mindestens 200 Pakete.",
     "**Auf dem Server selbst**: `ip -s link` zeigt Fehler und Drops an der Schnittstelle, `nstat` TCP-Retransmits – steigen sie auf einem Server und auf dem anderen nicht, liegt es nicht am Internet.",
     "**iperf3** zwischen den beiden Servern zeigt die echte Bandbreite; in beide Richtungen (`-R`) messen."],
    "Damit der Vergleich ehrlich ist, lassen wir dasselbe Skript auf beiden Servern dreimal laufen und heben die Dateien auf. Auf unserem VPS unterschieden sich zwei Läufe hintereinander um etwa 2 % – ein Unterschied von 30–50 % und mehr zwischen „gleichen“ Servern ist kein Messrauschen mehr.",
    [["Was", "Werkzeug", "Vergleichen", "Warnsignal"],
     ["Steal Time", "vmstat, mpstat, top", "`st` unter Last", "regelmäßig über 5–10 %"],
     ["CPU", "sysbench cpu, openssl speed", "events/s für 1 und alle Threads", "großer Abstand zum Zwilling; alle Threads ≪ ein Thread × vCPU"],
     ["Speicher", "sysbench memory", "MiB/s", "um ein Mehrfaches niedriger als beim Zwilling"],
     ["Platte, zufällig", "fio 4k randrw", "IOPS und `99.00th`", "IOPS um ein Mehrfaches niedriger; p99 im zweistelligen ms-Bereich"],
     ["Platte, sync", "fio fdatasync", "IOPS, sync-Latenz", "weit unter dem Zwilling – PostgreSQL-Commits werden langsam"],
     ["Platte, sequenziell", "dd, fio 1M, hdparm -t", "MB/s", "deutlich niedriger als beim Zwilling"],
     ["Netzwerk", "mtr, ping, iperf3, ip -s link", "Verlust am letzten Hop, RTT, Mbit/s, Drops", "Verlust bis zum Ziel, steigende Drops/Retransmits"]],
    ["**Rohausgaben beider Server** (die `bench-*.txt`-Dateien), die Uhrzeit jedes Laufs und die Server-IDs – nicht „Server 2 ist langsam“.",
     "**mtr in beide Richtungen** mit 200+ Paketen und Uhrzeit; bei Verlusten zusätzlich `ping -c 500` zum Server.",
     "**Eine konkrete Bitte**: den Host-Knoten des langsamen Servers prüfen oder den VPS auf einen anderen Knoten verschieben. Erwähnen, dass der Zwilling mit demselben Tarif um ein Mehrfaches schneller ist – dagegen lässt sich schwer argumentieren.",
     "**Tariftyp**: Contabo verkauft wie viele Anbieter VPS mit geteilten vCPU und eigene Produkte mit dedizierten Kernen (bei Contabo VDS). Bei geteilten Kernen ist etwas Schwankung normal, ein Mehrfaches nicht.",
     "**Jeden neuen Server direkt nach der Bestellung messen**, bevor etwas installiert wird: man hat eine Basislinie, und bei schlechtem Ergebnis kann man noch kündigen oder einen anderen Knoten verlangen, bevor Produktivdaten darauf liegen."],
    "Gleicher Tarif heißt nicht gleicher Server. Ein Skript, auf beiden Servern gleichzeitig und wiederholt ausgeführt, macht aus „fühlt sich langsam an“ Zahlen, mit denen der Support arbeiten kann. Für Odoo und PostgreSQL sind die wichtigen Werte Steal Time, fio-4k-p99-Latenz und fdatasync-IOPS. Diese Prüfungen machen wir bei jedem Server, den wir für Odoo einrichten – für Unternehmen in Deutschland, Österreich und der Schweiz.",
    "Links")

VPSBENCH["t"]["fr"] = _d(
    "Deux VPS identiques, l'un est lent : mesurer disque, CPU, mémoire et réseau sous Ubuntu",
    "Nous avons commandé deux VPS avec la même offre chez le même hébergeur – l'un était nettement plus lent et perdait des paquets. Comment le prouver avec des chiffres : dd, fio, hdparm, ioping et badblocks pour le disque, sysbench et openssl pour le CPU et la mémoire, le steal time, mtr, ping et iperf3 pour le réseau, un script prêt à l'emploi et quoi envoyer à l'hébergeur.",
    "Deux serveurs avec la même offre, la même image, commandés le même jour chez Contabo. L'un fonctionnait normalement, l'autre était lent en tout – et `mtr` montrait des paquets perdus. « Ça a l'air lent » ne permet rien au support. Il faut des chiffres des deux serveurs, mesurés de la même façon au même moment. Cet article est l'ensemble de mesures que nous utilisons pour cela.",
    "Toutes les commandes fonctionnent sous Ubuntu 22.04 / 24.04 (et Debian). Les sorties d'exemple viennent de notre propre VPS KVM (AMD EPYC, 4 vCPU, SSD) – elles montrent le format, ce ne sont pas des valeurs de référence. Les tests écrivent 1 à 2 Go de fichiers : ne pas les lancer sur un serveur de production aux heures de pointe.",
    ["Le cas", "Règles pour une comparaison honnête", "Steal time – la première chose à vérifier", "Disque : lecture et écriture", "CPU et mémoire", "Réseau : pertes et latence", "Tout dans un script", "Quoi envoyer à l'hébergeur", "Conclusion"],
    "Sur un VPS, on partage un hôte physique avec d'autres clients. L'offre garantit les vCPU, la RAM et la taille du disque, mais pas la charge du nœud hôte, la vitesse actuelle de son stockage ni l'occupation de sa liaison réseau. Deux VPS « identiques » peuvent atterrir sur des nœuds différents – avec une autre génération de CPU, un autre stockage et d'autres voisins. C'est exactement ce qu'il faut montrer.",
    ["**Mêmes commandes, mêmes versions** de fio et sysbench sur les deux serveurs – des chiffres de versions différentes ne sont pas comparables.",
     "**Au même moment, et plusieurs fois** : 3 passages à des heures différentes (matin, soir). Un voisin bruyant va et vient ; un seul passage ne prouve rien.",
     "**Serveurs au repos** : pas de sauvegardes, mises à jour ou tâches cron pendant le test (vérifier avec `top`). Sinon on se mesure soi-même.",
     "**Vérifier d'abord l'inventaire** : modèle de CPU, nombre de vCPU, RAM, noyau et type de disque – parfois la « même » offre est simplement un autre CPU."],
    "Le steal time est la part du temps pendant laquelle notre vCPU voulait tourner mais l'hyperviseur a donné le cœur physique à quelqu'un d'autre. C'est le signe le plus direct d'un nœud hôte surchargé, et sa mesure ne coûte rien.",
    ["`st` autour de 0 – correct. Régulièrement 5–10 % et plus sous charge – l'hôte est surréservé ; les mesures CPU sauteront d'un passage à l'autre.",
     "`wa` élevé pendant que le disque travaille – le processus attend le stockage ; voir les tests disque.",
     "`si`/`so` différents de 0 – le serveur swappe ; alors tous les tests sont faussés. Régler d'abord la mémoire."],
    "Pour un serveur avec une base de données (Odoo, PostgreSQL), le chiffre le plus important n'est pas le Mo/s d'un gros fichier, mais le nombre de petites opérations aléatoires par seconde et la durée des plus lentes. D'où plusieurs outils :",
    ["**dd** – simple, disponible partout, mais uniquement séquentiel. Toujours avec `oflag=direct`/`iflag=direct` ou `conv=fdatasync`, sinon on mesure la RAM. Un stockage qui compresse ou déduplique peut faire paraître `/dev/zero` plus rapide que de vraies données.",
     "**fio** – l'outil principal. `randrw 4k` avec `iodepth=32` montre les IOPS et la **latence au 99e percentile** (`99.00th`, en µs). Deux serveurs peuvent avoir des IOPS moyens proches alors que l'un a un p99 de plusieurs dizaines de millisecondes – c'est celui que les utilisateurs ressentent comme « Odoo bloque ».",
     "**fio avec fdatasync** – chaque écriture attend la confirmation du disque, exactement comme PostgreSQL au COMMIT. Un stockage réseau rapide sur le papier chute souvent ici.",
     "**hdparm -Tt** – un coup d'œil rapide ; sur un disque virtuel, `-t` mesure le chemin de stockage et le cache de l'hébergeur, donc seulement pour comparer les deux serveurs, pas comme valeur absolue.",
     "**ioping** – latence de requêtes isolées, utile à observer quelques minutes : un disque sain a un `mdev` stable.",
     "**badblocks** – cherche les secteurs défectueux d'un disque physique. Sur un VPS, il lit tout le disque virtuel pendant des heures et ne trouve rien que l'hébergeur ne verrait pas lui-même ; nous ne l'utilisons pas là. Et jamais `-w` sur un disque avec des données."],
    ["**sysbench cpu** avec un thread montre la vitesse d'un cœur, avec tous les threads – si les vCPU tournent vraiment en parallèle. Tous les threads devraient donner environ « un thread × vCPU ». Beaucoup moins signifie des cœurs partagés et occupés.",
     "**openssl speed** – un second avis sans rien installer ; comparer la dernière colonne.",
     "**sysbench memory** – bande passante mémoire ; un écart de plusieurs fois entre serveurs « identiques » signifie un autre hôte ou un hôte très chargé.",
     "Les workers Odoo exécutent Python dans un seul thread chacun – pour le temps de réponse d'une page, la valeur mono-thread compte plus que le total."],
    ["**Une perte seulement sur un saut intermédiaire n'est pas une perte.** Les routeurs répondent à l'ICMP avec une faible priorité ou pas du tout (`???`, 100 %). Ce qui compte, c'est le **dernier saut** : s'il est propre, le chemin est bon.",
     "**Une vraie perte** commence à un saut et continue jusqu'à la fin, en augmentant. Si elle commence dès les premiers sauts de l'hébergeur – réseau de l'hébergeur ou nœud hôte.",
     "**Les deux sens** : le chemin retour peut être différent. Lancer `mtr` du serveur vers l'extérieur et du bureau vers le serveur, au moins 200 paquets.",
     "**Sur le serveur lui-même** : `ip -s link` montre les erreurs et rejets de l'interface, `nstat` les retransmissions TCP – s'ils augmentent sur un serveur et pas sur l'autre, ce n'est pas Internet.",
     "**iperf3** entre les deux serveurs montre la bande passante réelle ; le lancer dans les deux sens (`-R`)."],
    "Pour une comparaison honnête, nous lançons le même script sur les deux serveurs, trois fois, et gardons les fichiers. Sur notre VPS, deux passages successifs différaient d'environ 2 % – un écart de 30–50 % ou plus entre serveurs « identiques » n'est plus du bruit de mesure.",
    [["Quoi", "Outil", "Comparer", "Signal d'alerte"],
     ["Steal time", "vmstat, mpstat, top", "`st` sous charge", "régulièrement au-dessus de 5–10 %"],
     ["CPU", "sysbench cpu, openssl speed", "events/s pour 1 et tous les threads", "grand écart avec le jumeau ; tous les threads ≪ un thread × vCPU"],
     ["Mémoire", "sysbench memory", "MiB/s", "plusieurs fois plus bas que le jumeau"],
     ["Disque, aléatoire", "fio 4k randrw", "IOPS et `99.00th`", "IOPS plusieurs fois plus bas ; p99 de plusieurs dizaines de ms"],
     ["Disque, sync", "fio fdatasync", "IOPS, latence sync", "loin sous le jumeau – les COMMIT PostgreSQL seront lents"],
     ["Disque, séquentiel", "dd, fio 1M, hdparm -t", "Mo/s", "nettement plus bas que le jumeau"],
     ["Réseau", "mtr, ping, iperf3, ip -s link", "perte au dernier saut, RTT, Mbit/s, rejets", "perte jusqu'à la destination, rejets/retransmissions en hausse"]],
    ["**Les sorties brutes des deux serveurs** (les fichiers `bench-*.txt`), l'heure de chaque passage et les identifiants des serveurs – pas « le serveur 2 est lent ».",
     "**mtr dans les deux sens** avec 200+ paquets et l'heure ; en cas de pertes, aussi `ping -c 500` vers le serveur.",
     "**Une demande concrète** : vérifier le nœud hôte du serveur lent, ou déplacer le VPS sur un autre nœud. Mentionner que le jumeau avec la même offre est plusieurs fois plus rapide – c'est difficile à contester.",
     "**Type d'offre** : Contabo, comme beaucoup d'hébergeurs, vend des VPS à vCPU partagés et des produits séparés à cœurs dédiés (chez Contabo : VDS). Sur des cœurs partagés, un peu de variation est normale ; un facteur de plusieurs ne l'est pas.",
     "**Mesurer chaque nouveau serveur juste après la commande**, avant d'installer quoi que ce soit : on a une référence, et si le résultat est mauvais on peut encore résilier ou demander un autre nœud avant que les données de production y soient."],
    "La même offre ne veut pas dire le même serveur. Un script, lancé sur les deux serveurs au même moment et répété, transforme « ça a l'air lent » en chiffres exploitables par le support. Pour Odoo et PostgreSQL, les valeurs à surveiller sont le steal time, la latence p99 de fio 4k et les IOPS fdatasync. Nous faisons ces vérifications pour chaque serveur que nous installons pour Odoo – pour des entreprises en Allemagne, en Autriche et en Suisse.",
    "Liens")

VPSBENCH["t"]["el"] = _d(
    "Δύο ίδιοι VPS, ο ένας είναι αργός: μέτρηση δίσκου, CPU, μνήμης και δικτύου στο Ubuntu",
    "Παραγγείλαμε δύο VPS με το ίδιο πακέτο από τον ίδιο πάροχο – ο ένας ήταν αισθητά πιο αργός και έχανε πακέτα. Πώς το αποδεικνύεις με αριθμούς: dd, fio, hdparm, ioping και badblocks για τον δίσκο, sysbench και openssl για CPU και μνήμη, steal time, mtr, ping και iperf3 για το δίκτυο, ένα έτοιμο script και τι στέλνεις στον πάροχο.",
    "Δύο server με το ίδιο πακέτο, την ίδια εικόνα, παραγγελμένοι την ίδια μέρα στη Contabo. Ο ένας δούλευε κανονικά, ο άλλος ήταν αργός σε όλα – και το `mtr` έδειχνε χαμένα πακέτα. Το «φαίνεται αργός» δεν βοηθά την υποστήριξη. Χρειάζονται αριθμοί και από τους δύο server, μετρημένοι με τον ίδιο τρόπο την ίδια ώρα. Αυτό το άρθρο είναι το σύνολο μετρήσεων που χρησιμοποιούμε γι' αυτό.",
    "Όλες οι εντολές δουλεύουν σε Ubuntu 22.04 / 24.04 (και Debian). Τα παραδείγματα εξόδου είναι από δικό μας KVM VPS (AMD EPYC, 4 vCPU, SSD) – δείχνουν τη μορφή, δεν είναι τιμές αναφοράς. Τα τεστ γράφουν 1–2 GB αρχεία: μην τα τρέχετε σε server παραγωγής σε ώρα αιχμής.",
    ["Η περίπτωση", "Κανόνες για δίκαιη σύγκριση", "Steal time – το πρώτο που ελέγχουμε", "Δίσκος: ανάγνωση και εγγραφή", "CPU και μνήμη", "Δίκτυο: απώλειες και καθυστέρηση", "Όλα σε ένα script", "Τι στέλνουμε στον πάροχο", "Συμπέρασμα"],
    "Σε έναν VPS μοιράζεστε έναν φυσικό host με άλλους πελάτες. Το πακέτο εγγυάται vCPU, RAM και μέγεθος δίσκου, αλλά όχι πόσο φορτωμένος είναι ο κόμβος, πόσο γρήγορος είναι τώρα ο αποθηκευτικός χώρος του ή πόσο γεμάτη η σύνδεση δικτύου του. Δύο «ίδιοι» VPS μπορεί να βρεθούν σε διαφορετικούς κόμβους – με άλλη γενιά CPU, άλλο storage και άλλους γείτονες. Αυτό ακριβώς πρέπει να δείξουμε.",
    ["**Ίδιες εντολές, ίδιες εκδόσεις** fio και sysbench και στους δύο server – αριθμοί από διαφορετικές εκδόσεις δεν συγκρίνονται.",
     "**Την ίδια ώρα, και επανειλημμένα**: 3 εκτελέσεις σε διαφορετικές ώρες (πρωί, βράδυ). Ένας θορυβώδης γείτονας έρχεται και φεύγει· μία εκτέλεση δεν αποδεικνύει τίποτα.",
     "**Server σε αδράνεια**: χωρίς backup, ενημερώσεις ή cron κατά το τεστ (έλεγχος με `top`). Αλλιώς μετράτε τον εαυτό σας.",
     "**Πρώτα ο εξοπλισμός**: μοντέλο CPU, πλήθος vCPU, RAM, πυρήνας και τύπος δίσκου – μερικές φορές το «ίδιο» πακέτο είναι απλώς άλλη CPU."],
    "Το steal time είναι το ποσοστό του χρόνου που η vCPU μας ήθελε να τρέξει αλλά ο hypervisor έδωσε τον φυσικό πυρήνα σε κάποιον άλλο. Είναι το πιο άμεσο σημάδι υπερφορτωμένου κόμβου, και η μέτρηση δεν κοστίζει τίποτα.",
    ["`st` γύρω στο 0 – εντάξει. Τακτικά 5–10 % και πάνω υπό φορτίο – ο host είναι υπερπωλημένος· οι μετρήσεις CPU θα πηδούν από εκτέλεση σε εκτέλεση.",
     "`wa` υψηλό όσο δουλεύει ο δίσκος – η διεργασία περιμένει το storage· δείτε τα τεστ δίσκου.",
     "`si`/`so` όχι 0 – ο server κάνει swap· τότε κάθε τεστ είναι λάθος. Πρώτα η μνήμη."],
    "Για server με βάση δεδομένων (Odoo, PostgreSQL) ο σημαντικότερος αριθμός δεν είναι τα MB/s ενός μεγάλου αρχείου, αλλά πόσες μικρές τυχαίες λειτουργίες ανά δευτερόλεπτο κάνει ο δίσκος και πόσο διαρκούν οι πιο αργές. Γι' αυτό υπάρχουν πολλά εργαλεία:",
    ["**dd** – απλό, παντού διαθέσιμο, αλλά μόνο σειριακό. Πάντα με `oflag=direct`/`iflag=direct` ή `conv=fdatasync`, αλλιώς μετράτε RAM. Storage που συμπιέζει ή κάνει deduplication μπορεί να κάνει το `/dev/zero` να φαίνεται ταχύτερο από πραγματικά δεδομένα.",
     "**fio** – το κύριο εργαλείο. Το `randrw 4k` με `iodepth=32` δείχνει IOPS και την **καθυστέρηση στο 99ο εκατοστημόριο** (`99.00th`, σε µs). Δύο server μπορεί να έχουν παρόμοια μέσα IOPS ενώ ο ένας έχει p99 δεκάδων χιλιοστών του δευτερολέπτου – αυτόν οι χρήστες τον νιώθουν ως «κολλάει το Odoo».",
     "**fio με fdatasync** – κάθε εγγραφή περιμένει επιβεβαίωση από τον δίσκο, όπως το PostgreSQL στο COMMIT. Δικτυακό storage, γρήγορο στα χαρτιά, συχνά πέφτει εδώ.",
     "**hdparm -Tt** – μια γρήγορη ματιά· σε εικονικό δίσκο το `-t` μετρά τη διαδρομή storage και την cache του παρόχου, άρα μόνο για σύγκριση των δύο server, όχι ως απόλυτη τιμή.",
     "**ioping** – καθυστέρηση μεμονωμένων αιτημάτων, καλό να το βλέπετε μερικά λεπτά: ένας υγιής δίσκος έχει σταθερό `mdev`.",
     "**badblocks** – ψάχνει χαλασμένους τομείς σε φυσικό δίσκο. Σε VPS διαβάζει για ώρες όλο τον εικονικό δίσκο και δεν βρίσκει τίποτα που δεν θα έβλεπε ο ίδιος ο πάροχος· εκεί δεν το χρησιμοποιούμε. Και ποτέ `-w` σε δίσκο με δεδομένα."],
    ["Το **sysbench cpu** με ένα thread δείχνει την ταχύτητα ενός πυρήνα, με όλα τα threads – αν οι vCPU τρέχουν πράγματι παράλληλα. Όλα τα threads πρέπει να δίνουν περίπου «ένα thread × vCPU». Πολύ λιγότερο σημαίνει μοιραζόμενους, απασχολημένους πυρήνες.",
     "**openssl speed** – δεύτερη γνώμη χωρίς εγκατάσταση· συγκρίνετε την τελευταία στήλη.",
     "**sysbench memory** – εύρος ζώνης μνήμης· διαφορά πολλαπλάσια ανάμεσα σε «ίδιους» server σημαίνει άλλο ή πολύ φορτωμένο host.",
     "Οι workers του Odoo τρέχουν Python σε ένα thread ο καθένας – για τον χρόνο απόκρισης μιας σελίδας μετράει περισσότερο η τιμή ενός thread παρά το σύνολο."],
    ["**Απώλεια μόνο σε ενδιάμεσο hop δεν είναι απώλεια.** Οι router απαντούν στο ICMP με χαμηλή προτεραιότητα ή καθόλου (`???`, 100 %). Σημασία έχει το **τελευταίο hop**: αν είναι καθαρό, η διαδρομή είναι εντάξει.",
     "**Πραγματική απώλεια** ξεκινά σε κάποιο hop και συνεχίζει ως το τέλος, αυξανόμενη. Αν ξεκινά από τα πρώτα hops του παρόχου – δίκτυο του παρόχου ή κόμβος.",
     "**Και οι δύο κατευθύνσεις**: η επιστροφή μπορεί να είναι άλλη διαδρομή. `mtr` από τον server προς τα έξω και από το γραφείο προς τον server, τουλάχιστον 200 πακέτα.",
     "**Στον ίδιο τον server**: το `ip -s link` δείχνει σφάλματα και drops στη διεπαφή, το `nstat` επαναμεταδόσεις TCP – αν αυξάνονται στον έναν server και όχι στον άλλο, δεν φταίει το διαδίκτυο.",
     "Το **iperf3** ανάμεσα στους δύο server δείχνει το πραγματικό εύρος ζώνης· και στις δύο κατευθύνσεις (`-R`)."],
    "Για τίμια σύγκριση τρέχουμε το ίδιο script και στους δύο server, τρεις φορές, και κρατάμε τα αρχεία. Στον δικό μας VPS δύο διαδοχικές εκτελέσεις διέφεραν περίπου 2 % – διαφορά 30–50 % ή περισσότερο ανάμεσα σε «ίδιους» server δεν είναι πια θόρυβος μέτρησης.",
    [["Τι", "Εργαλείο", "Σύγκριση", "Σήμα κινδύνου"],
     ["Steal time", "vmstat, mpstat, top", "`st` υπό φορτίο", "τακτικά πάνω από 5–10 %"],
     ["CPU", "sysbench cpu, openssl speed", "events/s για 1 και όλα τα threads", "μεγάλη απόσταση από τον δίδυμο· όλα τα threads ≪ ένα thread × vCPU"],
     ["Μνήμη", "sysbench memory", "MiB/s", "πολλαπλάσια χαμηλότερη από τον δίδυμο"],
     ["Δίσκος, τυχαία", "fio 4k randrw", "IOPS και `99.00th`", "IOPS πολλαπλάσια χαμηλότερα· p99 δεκάδων ms"],
     ["Δίσκος, sync", "fio fdatasync", "IOPS, καθυστέρηση sync", "πολύ κάτω από τον δίδυμο – τα COMMIT του PostgreSQL θα αργούν"],
     ["Δίσκος, σειριακά", "dd, fio 1M, hdparm -t", "MB/s", "αισθητά χαμηλότερα από τον δίδυμο"],
     ["Δίκτυο", "mtr, ping, iperf3, ip -s link", "απώλεια στο τελευταίο hop, RTT, Mbit/s, drops", "απώλεια ως τον προορισμό, αυξανόμενα drops/επαναμεταδόσεις"]],
    ["**Η ακατέργαστη έξοδος και των δύο server** (τα αρχεία `bench-*.txt`), η ώρα κάθε εκτέλεσης και τα ID των server – όχι «ο server 2 είναι αργός».",
     "**mtr και στις δύο κατευθύνσεις** με 200+ πακέτα και ώρα· για απώλειες και `ping -c 500` προς τον server.",
     "**Συγκεκριμένο αίτημα**: έλεγχος του κόμβου του αργού server ή μεταφορά του VPS σε άλλον κόμβο. Αναφέρετε ότι ο δίδυμος με το ίδιο πακέτο είναι πολλαπλάσια ταχύτερος – δύσκολο να αμφισβητηθεί.",
     "**Τύπος πακέτου**: η Contabo, όπως πολλοί πάροχοι, πουλά VPS με μοιραζόμενες vCPU και ξεχωριστά προϊόντα με αποκλειστικούς πυρήνες (στη Contabo: VDS). Σε μοιραζόμενους πυρήνες λίγη διακύμανση είναι φυσιολογική· πολλαπλάσια διαφορά όχι.",
     "**Μετράτε κάθε νέο server αμέσως μετά την παραγγελία**, πριν εγκαταστήσετε οτιδήποτε: έχετε σημείο αναφοράς, και αν το αποτέλεσμα είναι κακό μπορείτε ακόμη να ακυρώσετε ή να ζητήσετε άλλο κόμβο πριν μπουν δεδομένα παραγωγής."],
    "Το ίδιο πακέτο δεν σημαίνει τον ίδιο server. Ένα script, τρεγμένο και στους δύο server ταυτόχρονα και επανειλημμένα, κάνει το «φαίνεται αργό» αριθμούς με τους οποίους η υποστήριξη μπορεί να δουλέψει. Για Odoo και PostgreSQL οι τιμές που μετράνε είναι το steal time, η καθυστέρηση p99 του fio 4k και τα IOPS του fdatasync. Κάνουμε αυτούς τους ελέγχους σε κάθε server που στήνουμε για Odoo – για εταιρείες σε Γερμανία, Αυστρία και Ελβετία.",
    "Σύνδεσμοι")

VPSBENCH["t"]["uk"] = _d(
    "Два однакові VPS, один повільний: як виміряти диск, CPU, пам'ять і мережу в Ubuntu",
    "Ми замовили два VPS з однаковим тарифом в одного провайдера – один був помітно повільніший і губив пакети. Як довести це цифрами: dd, fio, hdparm, ioping і badblocks для диска, sysbench і openssl для CPU і пам'яті, steal time, mtr, ping та iperf3 для мережі, готовий скрипт і що надіслати провайдеру.",
    "Два сервери з однаковим тарифом, однаковим образом, замовлені в один день у Contabo. Один працював нормально, інший гальмував у всьому – а `mtr` показував втрачені пакети. «Здається, повільно» підтримці нічого не дає. Потрібні цифри з обох серверів, виміряні однаково й в один час. Ця стаття – набір вимірювань, який ми для цього використовуємо.",
    "Усі команди працюють в Ubuntu 22.04 / 24.04 (і Debian). Приклади виводу – з нашого власного KVM VPS (AMD EPYC, 4 vCPU, SSD): вони показують формат, а не еталонні значення. Тести записують 1–2 ГБ файлів: не запускайте їх на продакшн-сервері в пікові години.",
    ["Випадок", "Правила чесного порівняння", "Steal time – перше, що перевіряємо", "Диск: читання і запис", "CPU і пам'ять", "Мережа: втрати й затримка", "Усе в одному скрипті", "Що надіслати провайдеру", "Висновок"],
    "На VPS ви ділите фізичний хост з іншими клієнтами. Тариф гарантує vCPU, RAM і розмір диска, але не те, наскільки завантажений хост-вузол, наскільки швидке зараз його сховище чи наскільки заповнений мережевий канал. Два «однакові» VPS можуть опинитися на різних вузлах – з іншим поколінням CPU, іншим сховищем та іншими сусідами. Саме це й треба показати.",
    ["**Однакові команди, однакові версії** fio і sysbench на обох серверах – цифри з різних версій не порівнюються.",
     "**В один час і кілька разів**: 3 прогони в різні години (ранок, вечір). Шумний сусід приходить і йде; один прогін нічого не доводить.",
     "**Сервери без навантаження**: жодних бекапів, оновлень чи cron під час тесту (перевірте `top`). Інакше ви вимірюєте самі себе.",
     "**Спершу конфігурація**: модель CPU, кількість vCPU, RAM, ядро й тип диска – іноді «той самий» тариф – це просто інший CPU."],
    "Steal time – частка часу, коли наш vCPU хотів працювати, а гіпервізор віддав фізичне ядро комусь іншому. Це найпряміша ознака перевантаженого хост-вузла, і вимірювання нічого не коштує.",
    ["`st` близько 0 – нормально. Під навантаженням регулярно 5–10 % і більше – хост перепроданий; результати CPU стрибатимуть від прогону до прогону.",
     "`wa` високий, коли працює диск – процес чекає на сховище; дивіться тести диска.",
     "`si`/`so` не 0 – сервер свопить; тоді кожен тест хибний. Спочатку розберіться з пам'яттю."],
    "Для сервера з базою даних (Odoo, PostgreSQL) найважливіше число – не МБ/с великого файлу, а скільки дрібних випадкових операцій за секунду робить диск і скільки тривають найповільніші з них. Тому інструментів кілька:",
    ["**dd** – простий, є всюди, але лише послідовний. Завжди з `oflag=direct`/`iflag=direct` або `conv=fdatasync`, інакше вимірюєте RAM. Сховище, яке стискає чи дедуплікує, може показати `/dev/zero` швидшим за реальні дані.",
     "**fio** – головний інструмент. `randrw 4k` з `iodepth=32` показує IOPS і **затримку 99-го перцентиля** (`99.00th`, у мкс). Два сервери можуть мати схожі середні IOPS, а в одного p99 – десятки мілісекунд; саме це користувачі відчувають як «Odoo висне».",
     "**fio з fdatasync** – кожен запис чекає підтвердження диска, як PostgreSQL на COMMIT. Мережеве сховище, швидке на папері, тут часто провалюється.",
     "**hdparm -Tt** – швидкий погляд; на віртуальному диску `-t` вимірює шлях до сховища й кеш провайдера, тож лише для порівняння двох серверів, не як абсолютне значення.",
     "**ioping** – затримка окремих запитів, корисно дивитися кілька хвилин: у здорового диска стабільний `mdev`.",
     "**badblocks** – шукає биті сектори на фізичному диску. На VPS він годинами читає весь віртуальний диск і не знаходить нічого, чого не побачив би сам провайдер; там ми його не використовуємо. І ніколи `-w` на диску з даними."],
    ["**sysbench cpu** з одним потоком показує швидкість одного ядра, з усіма потоками – чи справді vCPU працюють паралельно. Усі потоки мають давати приблизно «один потік × vCPU». Значно менше – спільні ядра, які зайняті.",
     "**openssl speed** – друга думка без встановлення; порівнюйте останню колонку.",
     "**sysbench memory** – пропускна здатність пам'яті; різниця в рази між «однаковими» серверами означає інший або дуже завантажений хост.",
     "Воркери Odoo виконують Python в одному потоці кожен – для часу відповіді сторінки однопотокове значення важливіше за суму."],
    ["**Втрати лише на проміжному хопі – це не втрати.** Маршрутизатори відповідають на ICMP з низьким пріоритетом або не відповідають взагалі (`???`, 100 %). Важливий **останній хоп**: якщо там чисто – маршрут у порядку.",
     "**Справжні втрати** починаються на якомусь хопі й тягнуться до кінця, зростаючи. Якщо вони починаються з перших хопів провайдера – мережа провайдера або хост-вузол.",
     "**Обидва напрямки**: зворотний маршрут може бути іншим. Запускайте `mtr` із сервера назовні й з офісу до сервера, щонайменше 200 пакетів.",
     "**На самому сервері**: `ip -s link` показує помилки й drops на інтерфейсі, `nstat` – TCP-ретрансміти; якщо вони ростуть на одному сервері й не ростуть на іншому, справа не в інтернеті.",
     "**iperf3** між двома серверами показує реальну смугу; запускайте в обидва боки (`-R`)."],
    "Щоб порівняння було чесним, ми запускаємо той самий скрипт на обох серверах тричі й зберігаємо файли. На нашому VPS два прогони поспіль відрізнялися приблизно на 2 % – різниця 30–50 % і більше між «однаковими» серверами – уже не шум вимірювання.",
    [["Що", "Інструмент", "Порівнювати", "Тривожний сигнал"],
     ["Steal time", "vmstat, mpstat, top", "`st` під навантаженням", "регулярно понад 5–10 %"],
     ["CPU", "sysbench cpu, openssl speed", "events/s для 1 і всіх потоків", "великий розрив із близнюком; усі потоки ≪ один потік × vCPU"],
     ["Пам'ять", "sysbench memory", "MiB/s", "у рази нижче, ніж у близнюка"],
     ["Диск, випадково", "fio 4k randrw", "IOPS і `99.00th`", "IOPS у рази нижчі; p99 – десятки мс"],
     ["Диск, sync", "fio fdatasync", "IOPS, затримка sync", "значно нижче близнюка – COMMIT у PostgreSQL будуть повільні"],
     ["Диск, послідовно", "dd, fio 1M, hdparm -t", "МБ/с", "помітно нижче близнюка"],
     ["Мережа", "mtr, ping, iperf3, ip -s link", "втрати на останньому хопі, RTT, Мбіт/с, drops", "втрати до кінцевої точки, зростання drops/ретрансмітів"]],
    ["**Сирий вивід з обох серверів** (файли `bench-*.txt`), час кожного прогону та ID серверів – а не «сервер 2 повільний».",
     "**mtr в обидва боки** з 200+ пакетами й часом; при втратах ще `ping -c 500` до сервера.",
     "**Конкретне прохання**: перевірити хост-вузол повільного сервера або перенести VPS на інший вузол. Згадайте, що близнюк з тим самим тарифом у рази швидший – з цим важко сперечатися.",
     "**Тип тарифу**: Contabo, як і багато провайдерів, продає VPS зі спільними vCPU й окремі продукти з виділеними ядрами (у Contabo – VDS). На спільних ядрах певний розкид нормальний, різниця в рази – ні.",
     "**Вимірюйте кожен новий сервер одразу після замовлення**, до встановлення будь-чого: маєте базову лінію, а якщо результат поганий – ще можна відмовитися чи попросити інший вузол, поки там немає продакшн-даних."],
    "Однаковий тариф не означає однаковий сервер. Один скрипт, запущений на обох серверах одночасно й кілька разів, перетворює «здається, повільно» на цифри, з якими підтримка може працювати. Для Odoo і PostgreSQL головні значення – steal time, затримка p99 у fio 4k і IOPS fdatasync. Ці перевірки ми робимо для кожного сервера, який налаштовуємо під Odoo, – для компаній у Німеччині, Австрії та Швейцарії.",
    "Посилання")

VPSBENCH["t"]["ru"] = _d(
    "Два одинаковых VPS, один медленный: как измерить диск, CPU, память и сеть в Ubuntu",
    "Мы заказали два VPS с одинаковым тарифом у одного провайдера – один был заметно медленнее и терял пакеты. Как доказать это цифрами: dd, fio, hdparm, ioping и badblocks для диска, sysbench и openssl для CPU и памяти, steal time, mtr, ping и iperf3 для сети, готовый скрипт и что отправить провайдеру.",
    "Два сервера с одинаковым тарифом, одинаковым образом, заказаны в один день в Contabo. Один работал нормально, другой тормозил во всём – а `mtr` показывал потерянные пакеты. «Кажется, медленно» поддержке ничего не даёт. Нужны цифры с обоих серверов, измеренные одинаково и в одно время. Эта статья – набор измерений, который мы для этого используем.",
    "Все команды работают в Ubuntu 22.04 / 24.04 (и Debian). Примеры вывода – с нашего собственного KVM VPS (AMD EPYC, 4 vCPU, SSD): они показывают формат, а не эталонные значения. Тесты пишут 1–2 ГБ файлов: не запускайте их на продакшн-сервере в часы пик.",
    ["Случай", "Правила честного сравнения", "Steal time – первое, что проверяем", "Диск: чтение и запись", "CPU и память", "Сеть: потери и задержка", "Всё в одном скрипте", "Что отправить провайдеру", "Вывод"],
    "На VPS вы делите физический хост с другими клиентами. Тариф гарантирует vCPU, RAM и размер диска, но не то, насколько загружен хост-узел, насколько быстро сейчас его хранилище или насколько забит сетевой канал. Два «одинаковых» VPS могут оказаться на разных узлах – с другим поколением CPU, другим хранилищем и другими соседями. Именно это и надо показать.",
    ["**Одинаковые команды, одинаковые версии** fio и sysbench на обоих серверах – цифры разных версий не сравниваются.",
     "**В одно время и несколько раз**: 3 прогона в разные часы (утро, вечер). Шумный сосед приходит и уходит; один прогон ничего не доказывает.",
     "**Серверы без нагрузки**: никаких бэкапов, обновлений или cron во время теста (проверьте `top`). Иначе вы измеряете сами себя.",
     "**Сначала конфигурация**: модель CPU, число vCPU, RAM, ядро и тип диска – иногда «тот же» тариф – это просто другой CPU."],
    "Steal time – доля времени, когда наш vCPU хотел работать, а гипервизор отдал физическое ядро кому-то другому. Это самый прямой признак перегруженного хост-узла, и измерение ничего не стоит.",
    ["`st` около 0 – нормально. Под нагрузкой регулярно 5–10 % и больше – хост перепродан; результаты CPU будут скакать от прогона к прогону.",
     "`wa` высокий, когда работает диск – процесс ждёт хранилище; смотрите тесты диска.",
     "`si`/`so` не 0 – сервер свопит; тогда любой тест неверен. Сначала разберитесь с памятью."],
    "Для сервера с базой данных (Odoo, PostgreSQL) самое важное число – не МБ/с большого файла, а сколько мелких случайных операций в секунду делает диск и сколько длятся самые медленные из них. Поэтому инструментов несколько:",
    ["**dd** – простой, есть везде, но только последовательный. Всегда с `oflag=direct`/`iflag=direct` или `conv=fdatasync`, иначе вы измеряете RAM. Хранилище со сжатием или дедупликацией может показать `/dev/zero` быстрее реальных данных.",
     "**fio** – главный инструмент. `randrw 4k` с `iodepth=32` показывает IOPS и **задержку 99-го перцентиля** (`99.00th`, в мкс). У двух серверов могут быть похожие средние IOPS, а у одного p99 – десятки миллисекунд; именно это пользователи чувствуют как «Odoo виснет».",
     "**fio с fdatasync** – каждая запись ждёт подтверждения диска, как PostgreSQL на COMMIT. Сетевое хранилище, быстрое на бумаге, здесь часто проваливается.",
     "**hdparm -Tt** – быстрый взгляд; на виртуальном диске `-t` измеряет путь до хранилища и кеш провайдера, поэтому только для сравнения двух серверов, не как абсолютное значение.",
     "**ioping** – задержка отдельных запросов, полезно смотреть несколько минут: у здорового диска стабильный `mdev`.",
     "**badblocks** – ищет битые секторы на физическом диске. На VPS он часами читает весь виртуальный диск и не находит ничего, чего не увидел бы сам провайдер; там мы его не используем. И никогда `-w` на диске с данными."],
    ["**sysbench cpu** с одним потоком показывает скорость одного ядра, со всеми потоками – действительно ли vCPU работают параллельно. Все потоки должны давать примерно «один поток × vCPU». Заметно меньше – общие ядра, которые заняты.",
     "**openssl speed** – второе мнение без установки; сравнивайте последнюю колонку.",
     "**sysbench memory** – пропускная способность памяти; разница в разы между «одинаковыми» серверами означает другой или сильно загруженный хост.",
     "Воркеры Odoo выполняют Python в одном потоке каждый – для времени ответа страницы однопоточное значение важнее суммы."],
    ["**Потери только на промежуточном хопе – это не потери.** Маршрутизаторы отвечают на ICMP с низким приоритетом или не отвечают вовсе (`???`, 100 %). Важен **последний хоп**: если там чисто – маршрут в порядке.",
     "**Настоящие потери** начинаются на каком-то хопе и тянутся до конца, нарастая. Если они начинаются с первых хопов провайдера – сеть провайдера или хост-узел.",
     "**Оба направления**: обратный маршрут может быть другим. Запускайте `mtr` с сервера наружу и из офиса до сервера, минимум 200 пакетов.",
     "**На самом сервере**: `ip -s link` показывает ошибки и drops на интерфейсе, `nstat` – TCP-ретрансмиты; если они растут на одном сервере и не растут на другом, дело не в интернете.",
     "**iperf3** между двумя серверами показывает реальную полосу; запускайте в обе стороны (`-R`)."],
    "Чтобы сравнение было честным, мы запускаем один и тот же скрипт на обоих серверах трижды и сохраняем файлы. На нашем VPS два прогона подряд отличались примерно на 2 % – разница 30–50 % и больше между «одинаковыми» серверами – уже не шум измерения.",
    [["Что", "Инструмент", "Сравнивать", "Тревожный сигнал"],
     ["Steal time", "vmstat, mpstat, top", "`st` под нагрузкой", "регулярно выше 5–10 %"],
     ["CPU", "sysbench cpu, openssl speed", "events/s для 1 и всех потоков", "большой разрыв с близнецом; все потоки ≪ один поток × vCPU"],
     ["Память", "sysbench memory", "MiB/s", "в разы ниже, чем у близнеца"],
     ["Диск, случайно", "fio 4k randrw", "IOPS и `99.00th`", "IOPS в разы ниже; p99 – десятки мс"],
     ["Диск, sync", "fio fdatasync", "IOPS, задержка sync", "сильно ниже близнеца – COMMIT в PostgreSQL будут медленными"],
     ["Диск, последовательно", "dd, fio 1M, hdparm -t", "МБ/с", "заметно ниже близнеца"],
     ["Сеть", "mtr, ping, iperf3, ip -s link", "потери на последнем хопе, RTT, Мбит/с, drops", "потери до конечной точки, рост drops/ретрансмитов"]],
    ["**Сырой вывод с обоих серверов** (файлы `bench-*.txt`), время каждого прогона и ID серверов – а не «сервер 2 медленный».",
     "**mtr в обе стороны** с 200+ пакетами и временем; при потерях ещё `ping -c 500` до сервера.",
     "**Конкретная просьба**: проверить хост-узел медленного сервера или перенести VPS на другой узел. Упомяните, что близнец с тем же тарифом в разы быстрее – с этим трудно спорить.",
     "**Тип тарифа**: Contabo, как и многие провайдеры, продаёт VPS с общими vCPU и отдельные продукты с выделенными ядрами (у Contabo – VDS). На общих ядрах некоторый разброс нормален, разница в разы – нет.",
     "**Измеряйте каждый новый сервер сразу после заказа**, до установки чего-либо: у вас будет базовая линия, а если результат плохой – ещё можно отказаться или попросить другой узел, пока там нет продакшн-данных."],
    "Одинаковый тариф не означает одинаковый сервер. Один скрипт, запущенный на обоих серверах одновременно и несколько раз, превращает «кажется, медленно» в цифры, с которыми поддержка может работать. Для Odoo и PostgreSQL главные значения – steal time, задержка p99 в fio 4k и IOPS fdatasync. Эти проверки мы делаем для каждого сервера, который настраиваем под Odoo, – для компаний в Германии, Австрии и Швейцарии.",
    "Ссылки")
