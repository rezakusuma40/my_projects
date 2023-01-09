Big_Project: Muhammad Reza Adi Kusuma
02-01-2023

### Permasalahan
Cilvest, salah satu platform manajer investasi yang sedang ekspansi ingin melakukan ingest data dari Twitter untuk melihat seberapa besar demand masyarakat Indonesia dalam investasi. Ada beberapa instrumen investasi yang ingin diketahui demand-nya oleh Cilvest, yaitu saham, reksadana, dan sukuk. Data yang akan dianalisis adalah seberapa banyak orang berdiskusi terkait instrumen investasi yand disebutkan sebelumnya. Karena startup ini masih dalam tahap pengembangan, Cilvest menginginkan infrastruktur data dengan budget seefisien mungkin.
Cilvest menginginkan proses ingest data dilakukan secara streaming, dan data yang sudah diproses di-load ke Elasticsearch, Kibana, dan BigQuery.

### Data Flow Diagram
[![workflow-big-project.png](https://i.postimg.cc/Mp3xRTtc/workflow-big-project.png)](https://postimg.cc/FYS2XhMm)

#### Rancangan infrastruktur
Pada projek ini infrastruktur data akan dibangun di Google Cloud Platform (GCP), ada 4 tools yang akan digunakan di GCP:
1. Compute Engine, untuk melakukan streaming data ingestion secara kontinu
2. Cloud Storage, digunakan sebagai data lake
3. Dataproc, untuk melakukan batch processing dengan spark. 
4. BigQuery, digunakan sebagai data warehouse dan data mart

Untuk melakukan scraping data twitter, akan digunakan twitter API & modul tweepy. Proses streaming dilakukan dengan menggunakan Apache Kafka, program producer dan consumer dibangun dengan Python. Kafka dijalankan di Compute Engine Virtual Machine secara terus menerus. Data yang sudah di-ingest dengan kafka kemudian disimpan di Cloud Storage dalam bentuk yang masih cukup mentah.

Untuk analisis yang akan dilakukan, data yang tersimpan di Cloud Storage akan ditransformasi menggunakan Pyspark yang dijalankan di Dataproc. Proses transformasi dilakukan secara berkala. Untuk menghemat biaya, Dataproc cluster akan dibuat sebelum spark dijalankan, dan dihapus setelah dijalankan. Data yang sudah ditransformasi akan disimpan di BigQuery, Elasticsearch, dan Kibana.

Setelah data disimpan di BigQuery, akan dibuat tabel-tabel datamart dengan Python. Program ini dijalankan di Compute Engine Virtual Machine tepat setelah Dataproc dihapus. Data mart kemudian akan akan divisualisiasi menggunakan Looker Studio secara berkala.

#### Alasan Pemilihan Insfrastruktur Data
Alasan infrastruktur data ini didesain sedemikian rupa adalah untuk menjawab pertanyaan bisnis Cilvest, yaitu mengetahui seberapa besar demand masyarakat Indonesia terkait saham, reksadana, dan sukuk dengan mempertimbangkan efisiensi biaya.

Selain itu juga disesuaikan dengan data yang akan dianalisis. Karena yang akan dianalisis adalah data tweet masyarakat Indonesia, maka infrastruktur ini dedesain agar bisa mengambil data secara real time selama 24 jam setiap hari. Meskipun pada prakteknya ada jeda dalam melakukan scraping karena adanya pembatasan dari pihak twitter. Data yang disimpan di Cloud Storage masih berupa data mentah, agar bisa dipakai untuk berbagai analisis di masa mendatang.

Atribut yang diambil saat transformasi data adalah sebagai berikut:
1. id tweet, sebagai atribut unik dari setiap data
2. waktu pembuatan tweet, sebagai atribut waktu dari data 
3. username, akun yang melakukan tweet
4. tweet, teks tweet yang akan dibersihkan dan dianalisis.
5. language, untuk menyaring data tweet orang non-Indonesia karena tidak ada atribut yang benar-benar bisa menggambarkan lokasi

Setelah melakukan percobaan selama 4 hari, diestimasi jika ada sekitar 1500-2000 tweet unik yang masuk setiap hari, dengan ukuran rata-rata 10KB per data mentah (sekitar 15-20 MB per hari/450-600 MB per bulan/5,4-7,2 GB per tahun). Data tersebut bisa dikatakan tidak begitu besar, sehingga cukup digunakan mesin Compute Engine dengan RAM kecil, hal ini penting mengingat pemilihan mesin sangat berpengaruh pada biaya, sedangkan Virtual Machine Compute Engine perlu dijalankan terus menerus. Selain itu ukuran data yang sudah bersih terbilang sangat kecil, diestimasi sekitar 400 KB per hari/12 MB per bulan/ 144 MB per tahun.

Apache Kafka digunakan untuk melakukan streaming data ingestion, digunakan karena memiliki beberapa kelebihan diantaranya open-source, menggunakan sistem publish-subscribe, fault-tolerant, dan horizontally-scallable. Kafka dijalankan di Virtual Machine Compute Engine untuk menekan biaya.
Elasticsearch digunakan sebagai search engine yang akan digunakan oleh user, dipilih karena open-source dan memiliki kemampuan search engine yang sangat baik. Elasticsearch dijalankan di Virtual Machine Compute Engine agar bisa digunakan setiap saat jika diperlukan.
Transformasi data dilakukan dengan spark. Dijalankan dengan Dataproc karena powerful, memiliki sistem terdistribusi, tidak perlu menginstall spark, dan tidak menambah beban Compute Engine. Biaya Dataproc yang cenderung mahal dapat diatasi dengan hanya membuat Dataproc ketika akan dijalankan, yang diestimasi hanya perlu bekerja selama 5 menit per hari.
BigQuery digunakan sebagai data warehouse dan data mart karena serverless, murah, dan mudah untuk melakukan transfer data dengan produk GCP lainnya.
Looker Studio digunakan untuk membuat dashboard, dipilih karena mudah dikoneksikan dengan BigQuery, bisa auto-update, murah, dan mampu digunakan untuk membuat dashboard interaktif yang baik dan menarik.

### Spesifikasi Virtual Machine yang digunakan
#### Compute Engine
Name: Big_project
Region/Zone: us-central1-c
Machine type: e2-medium (2vCPU, 4 GB RAM)
Boot disk type: balance persistent disk
Disk size: 10GB
OS: Ubuntu 20.04 LTS
Python: 3.8.10
Zoo-keeper: 3.7.0
Kafka: 2.8.2
Elasticsearch: 8.5.2
Kibana: 8.5.2

#### Dataproc
Model: dataproc on compute engine
Name: Big_projects
Region/Zone: us-central1-c
OS: Ubuntu 18.04.06 LTS
Hadoop: 3.2
Spark: 3.1.3
Python: 3.8.15

##### Master Node
N = 1
Machine type: e2-standard-2 (2vCPU, 8 GB RAM)
Primary disk type: standard persistent disk
Disk size: 10GB

##### Worker Node
N = 3
Machine type: e2-standard-2 (2vCPU, 8 GB RAM)
Primary disk type: standard persistent disk
Disk size: 10GB

### Cara menjalankan Zookeeper dan Kafka di Background
1. Di jendela SSH, untuk menjalankan Zookeeper di background ketik command berikut:
    >. apache-zookeeper-3.7.0-bin/bin/zkServer.sh start
2. Jika sudah berhasil, lalu jalankan Kafka dengan mengetik command berikut:
    >cd kafka_2.13-2.8.2/
    >nohup bin/kafka-server-start.sh config/server.properties &

### Cara menjalankan Elasticsearch dan Kibana
1. Buka SSH Compute Engine
2. Di jendela SSH tersebut, untuk menjalankan Elasticsearch ketik command berikut:
    >sudo systemctl daemon-reload
    >sudo systemctl start elasticsearch
3. Di halaman Compute Engine, copy external IP dari VM yang digunakan
4. Buka tab baru di browser
5. Ketik external.IP.VM:9200 di URL (contoh: 35.205.154.5:9200)
6. Di jendela SSH sebelumnya, untuk menjalankan Kibana ketik command berikut:
    >sudo /bin/systemctl start kibana.service
7. Buka tab baru di browser
8. Ketik external.IP.VM:5601 di URL (contoh: 35.205.154.5:5601)
9. External IP setiap Virtual Machine berubah setiap dinyalakan ulang

### Menjalankan prd_big_project.py
Script ini berfungsi sebagai producer Kafka, digunakan untuk melakukan scraping data twitter ke topic secara streaming. Script ini dijalankan di Virtual Machine Compute Engine. Persiapan sebelum menjalankan script ini antara lain:
1. Mengupload file spark_big_project.py ke Virtual Machine Compute Engine
2. Perlu memiliki akun twitter developer dulu, jika belum bisa mendaftar di https://developer.twitter.com/.
3. Perlu menjalankan Zookeeper dan Kafka telebih dahulu
4. Perlu membuat topik "investasi". Jika belum ada, caranya dengan mengetik command berikut pada jendela SSH
    >cd kafka_2.13-2.8.2/
    >bin/kafka-topics.sh --zookeeper localhost:2181 --create --topic investasi --partitions 1 --replication-factor 1
5. Menyiapkan file 'twitterAPISulisB.json' berisi key dan token twitter API pribadi yang disimpan di Virtual Machine Compute Engine
6. Mengaktifkan virtual environment "venvbigproject", cara mengaktifkannya dengan mengetik command ini di jendela SSH:
    >. venvbigproject/bin/activate
7. Perlu menginstall modul tweepy dan kafka-python di virtual environment terlebih dahulu, cara menginstallnya dengan mengetik command ini di jendela SSH:
    >pip install tweepy
    >pip install kafka-python
8. Untuk menjalankan script ini di background, ketik command berikut di jendela SSH:
    >nohup python prd_big_project.py &

### Menjalankan csm_big_project.py
Script ini berfungsi sebagai consumer Kafka, digunakan untuk mengambil data dari topic ke Cloud Storage secara streaming. Script ini dijalankan di Virtual Machine Compute Engine. Persiapan sebelum menjalankan script ini antara lain:
1. Mengupload file spark_big_project.py ke Virtual Machine Compute Engine
2. Perlu membuat service account yang memiliki role admin Cloud Storage, service account disimpan di Compute Engine
3. Perlu menjalankan Zookeeper dan Kafka telebih dahulu
4. Perlu membuat topik "investasi" terlebih dahulu
5. Mengaktifkan virtual environment "venvbigproject"
6. Perlu menginstall modul kafka-python di virtual environment terlebih dahulu
7. Untuk menjalankan script ini di background, ketik command berikut di jendela SSH:
    >nohup python csm_big_project.py &

### Menjalankan spark_big_project.py
Script ini berfungsi untuk mengambil data twitter 1 hari sebelumnya dari Cloud Storage, melakukan transformasi, dan mengirim hasilnya ke Elasticsearch dan BigQuery (data warehouse). Script ini dijalankan di Virtual Machine Dataproc (master node). Persiapan sebelum menjalankan script ini antara lain:
1. Perlu membuat cluster Dataproc terlebih dahulu
2. Perlu menjalankan Elasticsearch, dan Kibana terlebih dahulu
3. Mengupload file spark_big_project.py ke Virtual Machine master node
4. Perlu membuat service account yang memiliki role admin Cloud Storage dan admin BigQuery, service account disimpan di Virtual Machine master node
5. Untuk menjalankan script ini ketik command berikut di jendela SSH:
    >spark-submit --packages org.elasticsearch:elasticsearch-spark-30_2.12:8.5.2,com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.27.1 spark_big_project.py

Setelah script ini berhasil dijalankan, cluster Dataproc tersebut dihapus. Proses di atas dilakukan setiap hari.

### Menjalankan big_project_datamart.py
Script ini berfungsi untuk membuat data mart dari data warehouse di BigQuery. Script ini dijalankan di Virtual Machine Compute Engine. Persiapan sebelum menjalankan script ini antara lain:
1. Perlu membuat service account yang memiliki role admin BigQuery, service account disimpan di Compute Engine
2. Berhasil menjalankan spark_big_project.py
3. Mengupload file spark_big_project.py ke Virtual Machine Compute Engine
4. Untuk menjalankan script ini di background, ketik command berikut di jendela SSH:
    >python big_project_datamart.py

### Visualisasi data
#### Elasticsearch:
1. Untuk melihat data yang masuk di Elasticsearch, lebih baik menggunakan Kibana
2. Buka kibana di browser
3. Klik menu -> Management -> Dev Tools
4. Di console ketik (jika sudah, lalu tekan ctrl+enter):
    ```json
    get covid_tweets_project5/_search
    ```

### Looker Studio
1. Jika dashboard belum dibuat, maka klik laporan kosong
2. Pada pilihan Google Connector, pilih BigQuery
3. Pilih project, dataset, dan table yang akan divisualisasi
4. Buat dashboard
5. Data akan otomatis diupdate setelah jeda tertentu

### Budget
Dengan rancangan infrastruktur ini, estimasi biaya yang dikeluarkan selama setahun adalah sebagai berikut:
Virtual Machine Compute Engine      : Rp 384.473,67
Virtual Machine Dataproc (master)   : Rp 3.160,06
Virtual Machine Dataproc (worker)   : Rp 9.480,17
Cloud Storage                       : Rp 805,91
BigQuery                            : Rp 0,00
Dataproc                            : Rp 3.772,56
Persistent Disk Compute Engine      : Rp 15.719,00
Persistent Disk Dataproc            : Rp 103,12
Total                               : Rp 417.514,48 per bulan/ Rp 5.010.173,76 per tahun

### Rekomendasi Pengembangan Infrastruktur Data
Di masa mendatang alangkah baiknya digunakan Apache Airflow untuk melakukan penjadwalan pada proses pembuatan/penghapusan Dataproc, transformasi dengan spark, dan pembuatan data mart. Apache Airflow akan dijalankan di Virtual Machine Compute Engine, untuk mengurangi beban Compute Engine dapat digunakan Pub/Sub sebagai alternatif menggantikan Kafka. Spesifikasi mesin dan storage Compute Engine dapat dikostumisasi untuk menyesuaikan volume data yang dapat terus meningkat di masa mendatang.
