# ATS CV Search Application

**Tugas Besar 3 IF2211 Strategi Algoritma**  
Pemanfaatan Pattern Matching untuk Membangun Sistem ATS Berbasis CV Digital

## 📋 Deskripsi

Aplikasi ATS (Applicant Tracking System) untuk mencari dan mencocokkan kata kunci dalam dokumen CV PDF menggunakan algoritma pattern matching: KMP, Boyer-Moore, Aho-Corasick, dan Levenshtein Distance.

## 🔍 Algoritma yang Diimplementasikan

### 1. Knuth-Morris-Pratt (KMP)
- **Kompleksitas**: O(n + m)
- **Keunggulan**: Efisien untuk pattern tunggal
- **Penggunaan**: Pencarian kata kunci exact matching

### 2. Boyer-Moore (BM)
- **Kompleksitas**: O(nm) worst case
- **Keunggulan**: Efisien untuk pattern panjang
- **Penggunaan**: Skip optimization pencarian

### 3. Aho-Corasick (Bonus)
- **Kompleksitas**: O(n + m + z)
- **Keunggulan**: Multi-pattern matching
- **Penggunaan**: Banyak kata kunci sekaligus

### 4. Levenshtein Distance
- **Kompleksitas**: O(n × m)
- **Keunggulan**: Fuzzy matching typo
- **Penggunaan**: Fallback exact matching

## 🛠️ Requirements

- **Docker & Docker Compose** (untuk MySQL database)
- **uv** (Python package manager)
- **Python 3.9+**

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd Tubes3_StimaSukses
```

### 2. Start MySQL Database
```bash
# Start MySQL dengan auto-initialization
./start_mysql.sh
# atau
docker-compose up -d mysql
```

### 3. Setup dan Jalankan Aplikasi
```bash
cd src
uv sync
uv run migrate_data.py  # Setup database schema
uv run main.py
```

## 🗄️ Database Management

### Auto-Initialization
Database schema dibuat otomatis menggunakan:
- `tubes3_seeding.sql` - Schema dan data lengkap
- `database/init/01_init_schema.sql` - Schema creation
- MySQL Docker container auto-setup

### Manual Database Operations
```bash
# Cek status database
docker exec ats_mysql mysqladmin ping -h localhost

# Akses database langsung
docker exec -it ats_mysql mysql -u ats_user -p kaggle_resumes

# Re-run schema jika diperlukan
docker exec -i ats_mysql mysql -u ats_user -p kaggle_resumes < tubes3_seeding.sql

# Reset database
docker-compose down -v && docker-compose up -d
```

### Database Schema
```sql
-- Table utama untuk applicant
CREATE TABLE ApplicantProfile (
    applicant_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    date_of_birth DATE,
    address VARCHAR(255),
    phone_number VARCHAR(20)
);

-- Table untuk CV details
CREATE TABLE ApplicationDetail (
    detail_id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT NOT NULL,
    application_role VARCHAR(100),
    cv_path TEXT,
    FOREIGN KEY (applicant_id) REFERENCES ApplicantProfile(applicant_id)
);
```

### Sample Data Insert
```bash
# Insert sample data untuk testing
docker exec -i ats_mysql mysql -u ats_user -p kaggle_resumes << 'EOF'
INSERT INTO ApplicantProfile (first_name, last_name, address, phone_number) VALUES 
('John', 'Doe', '123 Main St', '+1234567890'),
('Jane', 'Smith', '456 Oak Ave', '+0987654321');

INSERT INTO ApplicationDetail (applicant_id, application_role, cv_path) VALUES 
(1, 'Software Developer', 'data/INFORMATION-TECHNOLOGY/cv001.pdf'),
(2, 'Data Scientist', 'data/INFORMATION-TECHNOLOGY/cv002.pdf');
EOF
```

### Data Migration
```bash
# Run data migration script
cd src
uv run migrate_data.py

# Verify data
uv run -c "from database.repo import ResumeRepository; print(f'Found {len(ResumeRepository().get_all_resumes())} CVs')"
```

## 📁 Struktur Data

Pastikan folder `data/` berisi CV files:
```
data/
├── ACCOUNTANT/
├── ENGINEERING/
├── INFORMATION-TECHNOLOGY/
├── HR/
├── FINANCE/
└── ... (kategori lainnya)
```

## 💻 Cara Penggunaan

1. **Input Keywords**: Masukkan kata kunci dipisah koma
2. **Pilih Algoritma**: KMP, BM, AC, atau Levenshtein
3. **Set Parameters**: Jumlah hasil dan threshold fuzzy
4. **Search**: Klik tombol "🔍 Search CVs"
5. **View Results**: Lihat CV cards dengan Summary

## 🔧 Fitur Utama

- **Exact Matching**: KMP, Boyer-Moore, Aho-Corasick
- **Fuzzy Matching**: Levenshtein Distance
- **PDF Processing**: Ekstraksi teks otomatis
- **Database Integration**: MySQL untuk metadata CV
- **Information Extraction**: Regex untuk extract data
- **Performance Timing**: Monitoring waktu eksekusi

## 🐳 Docker Management

### Container Operations
```bash
# Start MySQL
./start_mysql.sh

# Stop services  
docker-compose down

# View logs
docker-compose logs mysql

# Restart container
docker-compose restart mysql
```

### Database Backup & Restore
```bash
# Backup database
docker exec ats_mysql mysqldump -u ats_user -p kaggle_resumes > backup.sql

# Restore database
docker exec -i ats_mysql mysql -u ats_user -p kaggle_resumes < backup.sql

# Reset database
docker-compose down -v && docker-compose up -d
```

## 🧪 Testing Algorithms

```bash
cd src
uv run algorithm/kmp.py      # Test KMP
uv run algorithm/bm.py       # Test Boyer-Moore
uv run algorithm/aho_corasick.py  # Test Aho-Corasick

# Test database connection
uv run -c "from database.mysql_config import MySQLConfig; print('DB OK' if MySQLConfig().test_connection() else 'DB FAIL')"
```

## 📊 Performance

| Algorithm | Pattern Length | Best For |
|-----------|----------------|----------|
| KMP | Any | Single pattern O(n+m) |
| Boyer-Moore | Long (>3 chars) | Skip characters |
| Aho-Corasick | Multiple | Many patterns |
| Levenshtein | Any | Typo tolerance |

## 🔧 Troubleshooting

### Database Issues
```bash
# Container not starting
docker-compose down && docker-compose up -d
docker-compose logs mysql

# Database connection refused
docker exec ats_mysql mysqladmin ping -h localhost

# Schema not applied
cd src && uv run migrate_data.py

# Reset everything
docker-compose down -v && docker-compose up -d
```

### Application Issues
```bash
# Dependencies issues
uv sync --reinstall

# Performance issues
# - Reduce CV count untuk testing
# - Use higher fuzzy threshold (80%+)
# - Choose appropriate algorithm
```

### Verify Setup
```bash
# Check MySQL container
docker ps | grep ats_mysql

# Check database tables
docker exec ats_mysql mysql -u ats_user -p kaggle_resumes -e "SHOW TABLES;"

# Check sample data
docker exec ats_mysql mysql -u ats_user -p kaggle_resumes -e "SELECT COUNT(*) FROM ApplicationDetail;"

# Test application connectivity
cd src && uv run -c "from database.repo import ResumeRepository; print(f'Found {len(ResumeRepository().get_all_resumes())} CVs')"
```

## 🔗 MySQL Connection Info

```bash
Host: localhost
Port: 3306
Database: kaggle_resumes
Username: ats_user
Password: StimaSukses
```

## 👥 Authors

**Tim Stima Sukses - IF2211 Strategi Algoritma ITB**

- **[Nama 1]** - NIM: [NIM] - KMP & Database
- **[Nama 2]** - NIM: [NIM] - Boyer-Moore & UI  
- **[Nama 3]** - NIM: [NIM] - Aho-Corasick & Regex

## 📝 License

Tugas Besar 3 IF2211 Strategi Algoritma - Institut Teknologi Bandung

---

**Note**: Database schema otomatis dibuat saat `docker-compose up -d`. Pastikan Docker running dan uv terinstall sebelum memulai aplikasi.