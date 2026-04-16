# Changelog

All notable changes to the AEX Omnimodule project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-04-16

### Added
- **Auto-expand and archive system** (`auto_expand_and_archive()`)
  - Automatic archiving when database exceeds 1.5GB
  - Automatic sealing of old cycles (2-year periods)
  - Automatic cleanup of expired data based on `max_history_months`
- **Dynamic cycle calculation** - Periods now auto-calculate based on current year
  - Format: `(year // 2) * 2` → `2026_2027`, `2028_2029`, etc.
  - Config example updated: `current_period: "auto"`
- **Database size warnings** in status view - shows databases exceeding 1GB
- **Database schema repair tool** (`fix_database_schema_v2.py`)
  - Automatic detection and repair of inconsistent database schemas
  - Field renaming: `credibility` → `credibility_score`
  - Type conversion: `weight REAL` → `weight INTEGER`
  - Adds missing `updated_at` field
  - Creates backup files before modification

### Fixed
- **Unified database naming** between `aex_admin.py` and `db_manager.py`
  - All database filenames are now strictly English
  - Chinese names only used for UI display (`chinese_name` field)
  - Standardized naming: `core_memory_YYYY_MM.db`, `core_knowledge_YYYY_MM.db`, `conversations_YYYY_MM.db`
- **Directory structure alignment** - Both managers now use same archive path structure
- **Period calculation consistency** - Fixed off-by-one error in cycle end year
- **Database schema inconsistencies** - Unified table structure across all databases
  - Fixed `CPlusPlus.db`, `Rust.db`, `Web.db` schema mismatches
  - Standardized `entries` table structure
  - Preserved all existing data during migration
- **Search functionality** - Knowledge retrieval now works correctly with repaired databases

### Changed
- `db_manager.py` now uses same path format as `aex_admin.py`
- Archive directory structure: `db/archive/{cycle}/` instead of `db/{period}/archive/`
- Status display now shows current cycle information
- Updated `.gitignore` to exclude `.db.backup` files

---

## [1.0.0] - 2026-04-15

### Added
- Initial release of AEX Omnimodule
- **AEX Admin Console** (`aex_admin.py`) - Complete management interface
  - Interactive menu system
  - Installation/uninstallation
  - Configuration management
  - Database management with pagination
  - SQL query execution
  - Backup and restore
  - Cycle-based archiving with SQLite VACUUM
- **Multi-database support**
  - `master.db` - Core system registry
  - `core_memory_YYYY_MM.db` - Emotion analysis history (monthly rotation)
  - `core_knowledge_YYYY_MM.db` - Knowledge storage (monthly rotation)
  - `conversations_YYYY_MM.db` - Conversation archives (monthly rotation)
  - `analytics.db` - Usage statistics
- **Identity/Personality system** - Customizable AI identity
  - Name, title, age, gender, personality
  - Background story, speaking style, catchphrase
  - Hobbies and preferences
- **2-year cycle archiving system**
  - Automatic period calculation
  - Sealed database support (read-only compressed)
  - LZMA compression for archived data
- **Python scripts**
  - `emotion_analyzer.py` - Text emotion detection
  - `search_learn.py` - Knowledge retrieval and learning
  - `db_manager.py` - Database operations
  - `security.py` - Access control
  - `init_system.py` - System initialization
- **Integration with qclaw-plugin** - AEX as sub-package with priority=0

### Technical
- SQLite3 with WAL mode for performance
- LZMA compression for archived databases
- Configurable via `config.json`
- Supports Python 3.8+

---

## Planned for Future

### [1.1.0] - TBD
- [ ] Automatic scheduled archiving (cron integration)
- [ ] Database replication/backup to cloud storage
- [ ] Advanced search with full-text indexing (FTS5)
- [ ] Migration tools for database format upgrades

### [1.2.0] - TBD
- [ ] Web-based admin dashboard
- [ ] Real-time monitoring and alerts
- [ ] Multi-node synchronization
