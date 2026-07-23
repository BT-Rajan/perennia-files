CREATE TABLE IF NOT EXISTS files (
    id                  CHAR(36)     NOT NULL PRIMARY KEY,
    current_version_id  CHAR(36)     NULL,
    status              ENUM('active','deleted') NOT NULL DEFAULT 'active',
    created_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    created_by          CHAR(36)     NULL,
    deleted_at          DATETIME(6)  NULL,
    deleted_by          CHAR(36)     NULL,
    KEY idx_files_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS file_versions (
    id                  CHAR(36)     NOT NULL PRIMARY KEY,
    file_id             CHAR(36)     NOT NULL,
    version_number      INT UNSIGNED NOT NULL,
    original_filename   VARCHAR(255) NOT NULL,
    extension           VARCHAR(16)  NOT NULL,
    mime_type           VARCHAR(128) NOT NULL,
    size_bytes          BIGINT UNSIGNED NOT NULL,
    checksum_algorithm  VARCHAR(16)  NOT NULL DEFAULT 'sha256',
    checksum            CHAR(64)     NOT NULL,
    storage_reference   VARCHAR(255) NOT NULL,
    encrypted           TINYINT(1)   NOT NULL DEFAULT 0,
    created_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    created_by          CHAR(36)     NULL,
    UNIQUE KEY uq_file_version (file_id, version_number),
    KEY idx_versions_file (file_id),
    CONSTRAINT fk_versions_file FOREIGN KEY (file_id)
        REFERENCES files(id) ON DELETE CASCADE
) ENGINE=InnoDB;

ALTER TABLE files
    ADD CONSTRAINT fk_files_current_version FOREIGN KEY (current_version_id)
        REFERENCES file_versions(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS file_extracted_content (
    id                  CHAR(36)     NOT NULL PRIMARY KEY,
    source_file_id      CHAR(36)     NOT NULL,
    source_version_id   CHAR(36)     NOT NULL,
    processor           VARCHAR(64)  NOT NULL,
    content             LONGTEXT     NOT NULL,
    created_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    KEY idx_extracted_version (source_version_id),
    CONSTRAINT fk_extracted_file FOREIGN KEY (source_file_id)
        REFERENCES files(id) ON DELETE CASCADE,
    CONSTRAINT fk_extracted_version FOREIGN KEY (source_version_id)
        REFERENCES file_versions(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS file_summaries (
    id                  CHAR(36)     NOT NULL PRIMARY KEY,
    source_file_id      CHAR(36)     NOT NULL,
    source_version_id   CHAR(36)     NOT NULL,
    processor           VARCHAR(64)  NOT NULL,
    content             LONGTEXT     NOT NULL,
    created_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    KEY idx_summaries_version (source_version_id),
    CONSTRAINT fk_summaries_file FOREIGN KEY (source_file_id)
        REFERENCES files(id) ON DELETE CASCADE,
    CONSTRAINT fk_summaries_version FOREIGN KEY (source_version_id)
        REFERENCES file_versions(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS file_qa_results (
    id                  CHAR(36)     NOT NULL PRIMARY KEY,
    source_file_id      CHAR(36)     NOT NULL,
    source_version_id   CHAR(36)     NOT NULL,
    processor           VARCHAR(64)  NOT NULL,
    question            TEXT         NOT NULL,
    answer              LONGTEXT     NOT NULL,
    created_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    KEY idx_qa_version (source_version_id),
    CONSTRAINT fk_qa_file FOREIGN KEY (source_file_id)
        REFERENCES files(id) ON DELETE CASCADE,
    CONSTRAINT fk_qa_version FOREIGN KEY (source_version_id)
        REFERENCES file_versions(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS file_generated_content (
    id                  CHAR(36)     NOT NULL PRIMARY KEY,
    source_file_id      CHAR(36)     NOT NULL,
    source_version_id   CHAR(36)     NOT NULL,
    processor           VARCHAR(64)  NOT NULL,
    instruction         TEXT         NOT NULL,
    content             LONGTEXT     NOT NULL,
    created_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    KEY idx_generated_version (source_version_id),
    CONSTRAINT fk_generated_file FOREIGN KEY (source_file_id)
        REFERENCES files(id) ON DELETE CASCADE,
    CONSTRAINT fk_generated_version FOREIGN KEY (source_version_id)
        REFERENCES file_versions(id) ON DELETE CASCADE
) ENGINE=InnoDB;
