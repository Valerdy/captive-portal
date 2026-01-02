-- =============================================================================
-- CAPTIVE PORTAL - SCHÉMA DE BASE DE DONNÉES COMPLET
-- =============================================================================
-- Généré automatiquement à partir des modèles Django
-- Date: 2026-01-01
-- Version: 1.0
-- =============================================================================

-- =============================================================================
-- LÉGENDE
-- =============================================================================
-- PK = Clé Primaire (Primary Key)
-- FK = Clé Étrangère (Foreign Key)
-- UQ = Contrainte d'unicité (Unique)
-- NN = Non Null (Not Null)
-- DF = Valeur par défaut (Default)
-- IDX = Index
-- =============================================================================

-- #############################################################################
-- APPLICATION CORE - Tables principales de gestion
-- #############################################################################

-- =============================================================================
-- Table: core_profile
-- Description: Profils de connexion définissant les quotas et restrictions
-- =============================================================================
CREATE TABLE core_profile (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    name                    VARCHAR(100) NOT NULL UNIQUE,             -- NN, UQ
    description             TEXT,
    bandwidth_download      INTEGER NOT NULL DEFAULT 10,              -- NN, DF (Mbps)
    bandwidth_upload        INTEGER NOT NULL DEFAULT 5,               -- NN, DF (Mbps)
    session_timeout         INTEGER NOT NULL DEFAULT 3600,            -- NN, DF (secondes)
    idle_timeout            INTEGER NOT NULL DEFAULT 600,             -- NN, DF (secondes)
    daily_quota             BIGINT DEFAULT 1073741824,                -- DF (1 GB en bytes)
    weekly_quota            BIGINT,
    monthly_quota           BIGINT,
    max_devices             INTEGER NOT NULL DEFAULT 3,               -- NN, DF
    priority                INTEGER NOT NULL DEFAULT 1,               -- NN, DF
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    allow_social_media      BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    allow_streaming         BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    allow_gaming            BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    allow_downloads         BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_profile_is_active ON core_profile(is_active);
CREATE INDEX idx_profile_priority ON core_profile(priority);

-- =============================================================================
-- Table: core_promotion
-- Description: Groupes/promotions d'utilisateurs (ex: classes, départements)
-- =============================================================================
CREATE TABLE core_promotion (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    name                    VARCHAR(100) NOT NULL UNIQUE,             -- NN, UQ
    description             TEXT,
    profile_id              BIGINT REFERENCES core_profile(id)        -- FK → core_profile
                            ON DELETE SET NULL,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    max_users               INTEGER,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_promotion_profile_id ON core_promotion(profile_id);
CREATE INDEX idx_promotion_is_active ON core_promotion(is_active);

-- =============================================================================
-- Table: core_user
-- Description: Utilisateurs du portail captif (étend AbstractUser)
-- =============================================================================
CREATE TABLE core_user (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    password                VARCHAR(128) NOT NULL,                    -- NN (Django auth)
    last_login              TIMESTAMP WITH TIME ZONE,
    is_superuser            BOOLEAN NOT NULL DEFAULT FALSE,           -- NN, DF
    username                VARCHAR(150) NOT NULL UNIQUE,             -- NN, UQ
    first_name              VARCHAR(150) NOT NULL DEFAULT '',         -- NN, DF
    last_name               VARCHAR(150) NOT NULL DEFAULT '',         -- NN, DF
    email                   VARCHAR(254) NOT NULL DEFAULT '',         -- NN, DF
    is_staff                BOOLEAN NOT NULL DEFAULT FALSE,           -- NN, DF
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    date_joined             TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Champs personnalisés
    phone_number            VARCHAR(20),
    promotion_id            BIGINT REFERENCES core_promotion(id)      -- FK → core_promotion
                            ON DELETE SET NULL,
    profile_id              BIGINT REFERENCES core_profile(id)        -- FK → core_profile
                            ON DELETE SET NULL,
    cleartext_password      VARCHAR(255),                             -- Pour RADIUS
    is_radius_activated     BOOLEAN NOT NULL DEFAULT FALSE,           -- NN, DF
    is_radius_enabled       BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    radius_activated_at     TIMESTAMP WITH TIME ZONE,
    mac_address             VARCHAR(17),                              -- Format: XX:XX:XX:XX:XX:XX
    expires_at              TIMESTAMP WITH TIME ZONE,
    created_by_id           BIGINT REFERENCES core_user(id)           -- FK → self
                            ON DELETE SET NULL,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_username ON core_user(username);
CREATE INDEX idx_user_promotion_id ON core_user(promotion_id);
CREATE INDEX idx_user_profile_id ON core_user(profile_id);
CREATE INDEX idx_user_is_radius_activated ON core_user(is_radius_activated);
CREATE INDEX idx_user_is_active ON core_user(is_active);
CREATE INDEX idx_user_created_by_id ON core_user(created_by_id);
-- Index composites pour optimisation
CREATE INDEX idx_user_active_radius ON core_user(is_active, is_radius_activated);
CREATE INDEX idx_user_promotion_active ON core_user(promotion_id, is_active);
CREATE INDEX idx_user_expires_active ON core_user(expires_at, is_active);

-- =============================================================================
-- Table: core_device
-- Description: Appareils des utilisateurs (MAC binding)
-- =============================================================================
CREATE TABLE core_device (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    user_id                 BIGINT NOT NULL REFERENCES core_user(id)  -- FK → core_user
                            ON DELETE CASCADE,
    name                    VARCHAR(100) NOT NULL,                    -- NN
    mac_address             VARCHAR(17) NOT NULL,                     -- NN, Format: XX:XX:XX:XX:XX:XX
    ip_address              INET,
    device_type             VARCHAR(50) DEFAULT 'unknown',            -- DF
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    is_blocked              BOOLEAN NOT NULL DEFAULT FALSE,           -- NN, DF
    last_seen               TIMESTAMP WITH TIME ZONE,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_device_user_mac UNIQUE(user_id, mac_address)        -- UQ
);

CREATE INDEX idx_device_user_id ON core_device(user_id);
CREATE INDEX idx_device_mac_address ON core_device(mac_address);
CREATE INDEX idx_device_is_active ON core_device(is_active);

-- =============================================================================
-- Table: core_session
-- Description: Sessions de connexion des utilisateurs
-- =============================================================================
CREATE TABLE core_session (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    user_id                 BIGINT NOT NULL REFERENCES core_user(id)  -- FK → core_user
                            ON DELETE CASCADE,
    device_id               BIGINT REFERENCES core_device(id)         -- FK → core_device
                            ON DELETE SET NULL,
    session_id              VARCHAR(255) NOT NULL UNIQUE,             -- NN, UQ (RADIUS Acct-Session-Id)
    nas_ip_address          INET,
    nas_port                INTEGER,
    framed_ip_address       INET,
    called_station_id       VARCHAR(50),
    calling_station_id      VARCHAR(50),                              -- MAC client
    status                  VARCHAR(20) NOT NULL DEFAULT 'active',    -- NN, DF
    started_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at                TIMESTAMP WITH TIME ZONE,
    session_time            INTEGER DEFAULT 0,                        -- Durée en secondes
    input_octets            BIGINT DEFAULT 0,                         -- Bytes reçus
    output_octets           BIGINT DEFAULT 0,                         -- Bytes envoyés
    terminate_cause         VARCHAR(100),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_session_user_id ON core_session(user_id);
CREATE INDEX idx_session_device_id ON core_session(device_id);
CREATE INDEX idx_session_session_id ON core_session(session_id);
CREATE INDEX idx_session_status ON core_session(status);
CREATE INDEX idx_session_started_at ON core_session(started_at);

-- =============================================================================
-- Table: core_voucher
-- Description: Vouchers prépayés pour accès temporaire
-- =============================================================================
CREATE TABLE core_voucher (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    code                    VARCHAR(20) NOT NULL UNIQUE,              -- NN, UQ
    profile_id              BIGINT NOT NULL REFERENCES core_profile(id) -- FK → core_profile
                            ON DELETE CASCADE,
    duration_hours          INTEGER NOT NULL DEFAULT 24,              -- NN, DF
    max_uses                INTEGER NOT NULL DEFAULT 1,               -- NN, DF
    current_uses            INTEGER NOT NULL DEFAULT 0,               -- NN, DF
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    valid_from              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    valid_until             TIMESTAMP WITH TIME ZONE,
    created_by_id           BIGINT REFERENCES core_user(id)           -- FK → core_user
                            ON DELETE SET NULL,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_voucher_code ON core_voucher(code);
CREATE INDEX idx_voucher_profile_id ON core_voucher(profile_id);
CREATE INDEX idx_voucher_is_active ON core_voucher(is_active);
CREATE INDEX idx_voucher_created_by_id ON core_voucher(created_by_id);

-- =============================================================================
-- Table: core_blockedsite
-- Description: Sites bloqués par profil ou promotion
-- =============================================================================
CREATE TABLE core_blockedsite (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    domain                  VARCHAR(255) NOT NULL,                    -- NN
    category                VARCHAR(50) DEFAULT 'other',              -- DF
    reason                  TEXT,
    profile_id              BIGINT REFERENCES core_profile(id)        -- FK → core_profile
                            ON DELETE CASCADE,
    promotion_id            BIGINT REFERENCES core_promotion(id)      -- FK → core_promotion
                            ON DELETE CASCADE,
    is_global               BOOLEAN NOT NULL DEFAULT FALSE,           -- NN, DF
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    created_by_id           BIGINT REFERENCES core_user(id)           -- FK → core_user
                            ON DELETE SET NULL,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_blockedsite_domain ON core_blockedsite(domain);
CREATE INDEX idx_blockedsite_profile_id ON core_blockedsite(profile_id);
CREATE INDEX idx_blockedsite_promotion_id ON core_blockedsite(promotion_id);
CREATE INDEX idx_blockedsite_is_global ON core_blockedsite(is_global);
CREATE INDEX idx_blockedsite_is_active ON core_blockedsite(is_active);

-- =============================================================================
-- Table: core_userquota
-- Description: Suivi des quotas de données des utilisateurs
-- =============================================================================
CREATE TABLE core_userquota (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    user_id                 BIGINT NOT NULL UNIQUE REFERENCES core_user(id) -- FK, UQ → core_user
                            ON DELETE CASCADE,
    daily_used              BIGINT NOT NULL DEFAULT 0,                -- NN, DF
    weekly_used             BIGINT NOT NULL DEFAULT 0,                -- NN, DF
    monthly_used            BIGINT NOT NULL DEFAULT 0,                -- NN, DF
    total_used              BIGINT NOT NULL DEFAULT 0,                -- NN, DF
    last_reset_daily        DATE NOT NULL DEFAULT CURRENT_DATE,       -- NN, DF
    last_reset_weekly       DATE NOT NULL DEFAULT CURRENT_DATE,       -- NN, DF
    last_reset_monthly      DATE NOT NULL DEFAULT CURRENT_DATE,       -- NN, DF
    is_quota_exceeded       BOOLEAN NOT NULL DEFAULT FALSE,           -- NN, DF
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Table: core_userprofileusage
-- Description: Historique d'utilisation des profils par utilisateur
-- =============================================================================
CREATE TABLE core_userprofileusage (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    user_id                 BIGINT NOT NULL REFERENCES core_user(id)  -- FK → core_user
                            ON DELETE CASCADE,
    profile_id              BIGINT NOT NULL REFERENCES core_profile(id) -- FK → core_profile
                            ON DELETE CASCADE,
    date                    DATE NOT NULL,                            -- NN
    session_count           INTEGER NOT NULL DEFAULT 0,               -- NN, DF
    total_session_time      INTEGER NOT NULL DEFAULT 0,               -- NN, DF (secondes)
    total_input_octets      BIGINT NOT NULL DEFAULT 0,                -- NN, DF
    total_output_octets     BIGINT NOT NULL DEFAULT 0,                -- NN, DF
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_usage_user_profile_date UNIQUE(user_id, profile_id, date)
);

CREATE INDEX idx_userprofileusage_user_id ON core_userprofileusage(user_id);
CREATE INDEX idx_userprofileusage_profile_id ON core_userprofileusage(profile_id);
CREATE INDEX idx_userprofileusage_date ON core_userprofileusage(date);

-- =============================================================================
-- Table: core_profilehistory
-- Description: Historique des changements de profil
-- =============================================================================
CREATE TABLE core_profilehistory (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    user_id                 BIGINT NOT NULL REFERENCES core_user(id)  -- FK → core_user
                            ON DELETE CASCADE,
    old_profile_id          BIGINT REFERENCES core_profile(id)        -- FK → core_profile
                            ON DELETE SET NULL,
    new_profile_id          BIGINT REFERENCES core_profile(id)        -- FK → core_profile
                            ON DELETE SET NULL,
    reason                  TEXT,
    changed_by_id           BIGINT REFERENCES core_user(id)           -- FK → core_user
                            ON DELETE SET NULL,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_profilehistory_user_id ON core_profilehistory(user_id);
CREATE INDEX idx_profilehistory_created_at ON core_profilehistory(created_at);

-- =============================================================================
-- Table: core_profilealert
-- Description: Alertes liées aux profils (quota atteint, etc.)
-- =============================================================================
CREATE TABLE core_profilealert (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    user_id                 BIGINT NOT NULL REFERENCES core_user(id)  -- FK → core_user
                            ON DELETE CASCADE,
    profile_id              BIGINT REFERENCES core_profile(id)        -- FK → core_profile
                            ON DELETE SET NULL,
    alert_type              VARCHAR(50) NOT NULL,                     -- NN
    message                 TEXT NOT NULL,                            -- NN
    is_read                 BOOLEAN NOT NULL DEFAULT FALSE,           -- NN, DF
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_profilealert_user_id ON core_profilealert(user_id);
CREATE INDEX idx_profilealert_is_read ON core_profilealert(is_read);
CREATE INDEX idx_profilealert_created_at ON core_profilealert(created_at);

-- =============================================================================
-- Table: core_userdisconnectionlog
-- Description: Journal des déconnexions utilisateur
-- =============================================================================
CREATE TABLE core_userdisconnectionlog (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    user_id                 BIGINT NOT NULL REFERENCES core_user(id)  -- FK → core_user
                            ON DELETE CASCADE,
    session_id              BIGINT REFERENCES core_session(id)        -- FK → core_session
                            ON DELETE SET NULL,
    reason                  VARCHAR(100) NOT NULL,                    -- NN
    details                 TEXT,
    initiated_by            VARCHAR(50) NOT NULL DEFAULT 'system',    -- NN, DF
    success                 BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_userdisconnectionlog_user_id ON core_userdisconnectionlog(user_id);
CREATE INDEX idx_userdisconnectionlog_created_at ON core_userdisconnectionlog(created_at);

-- =============================================================================
-- Table: core_adminauditlog
-- Description: Journal d'audit des actions administratives
-- =============================================================================
CREATE TABLE core_adminauditlog (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    admin_id                BIGINT REFERENCES core_user(id)           -- FK → core_user
                            ON DELETE SET NULL,
    action                  VARCHAR(100) NOT NULL,                    -- NN
    model_name              VARCHAR(100),
    object_id               VARCHAR(100),
    object_repr             VARCHAR(255),
    changes                 JSONB,                                    -- Détails des modifications
    ip_address              INET,
    user_agent              VARCHAR(500),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_adminauditlog_admin_id ON core_adminauditlog(admin_id);
CREATE INDEX idx_adminauditlog_action ON core_adminauditlog(action);
CREATE INDEX idx_adminauditlog_model_name ON core_adminauditlog(model_name);
CREATE INDEX idx_adminauditlog_created_at ON core_adminauditlog(created_at);

-- =============================================================================
-- Table: core_syncfailurelog
-- Description: Journal des échecs de synchronisation (RADIUS, MikroTik)
-- =============================================================================
CREATE TABLE core_syncfailurelog (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    sync_type               VARCHAR(50) NOT NULL,                     -- NN (radius_user, radius_profile, mikrotik_hotspot)
    source_model            VARCHAR(100) NOT NULL,                    -- NN
    source_id               VARCHAR(100) NOT NULL,                    -- NN
    source_repr             VARCHAR(255),
    error_message           TEXT NOT NULL,                            -- NN
    error_traceback         TEXT,
    context                 JSONB,
    status                  VARCHAR(20) NOT NULL DEFAULT 'pending',   -- NN, DF (pending, retrying, resolved, failed, ignored)
    retry_count             INTEGER NOT NULL DEFAULT 0,               -- NN, DF
    max_retries             INTEGER NOT NULL DEFAULT 3,               -- NN, DF
    next_retry_at           TIMESTAMP WITH TIME ZONE,
    resolved_at             TIMESTAMP WITH TIME ZONE,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_syncfailurelog_sync_type ON core_syncfailurelog(sync_type);
CREATE INDEX idx_syncfailurelog_status ON core_syncfailurelog(status);
CREATE INDEX idx_syncfailurelog_next_retry_at ON core_syncfailurelog(next_retry_at);
CREATE INDEX idx_syncfailurelog_source ON core_syncfailurelog(source_model, source_id);


-- #############################################################################
-- APPLICATION RADIUS - Tables FreeRADIUS
-- #############################################################################

-- =============================================================================
-- Table: radius_radiusserver
-- Description: Configuration des serveurs RADIUS
-- =============================================================================
CREATE TABLE radius_radiusserver (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    name                    VARCHAR(100) NOT NULL UNIQUE,             -- NN, UQ
    host                    VARCHAR(255) NOT NULL,                    -- NN
    auth_port               INTEGER NOT NULL DEFAULT 1812,            -- NN, DF
    acct_port               INTEGER NOT NULL DEFAULT 1813,            -- NN, DF
    secret                  VARCHAR(255) NOT NULL,                    -- NN (chiffré)
    is_primary              BOOLEAN NOT NULL DEFAULT FALSE,           -- NN, DF
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    timeout                 INTEGER NOT NULL DEFAULT 5,               -- NN, DF (secondes)
    retries                 INTEGER NOT NULL DEFAULT 3,               -- NN, DF
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Table: radius_radiusauthlog
-- Description: Journal des authentifications RADIUS
-- =============================================================================
CREATE TABLE radius_radiusauthlog (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    username                VARCHAR(150) NOT NULL,                    -- NN
    nas_ip_address          INET,
    nas_port                INTEGER,
    calling_station_id      VARCHAR(50),                              -- MAC client
    auth_type               VARCHAR(50),
    status                  VARCHAR(20) NOT NULL,                     -- NN (success, reject, error)
    reply_message           TEXT,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_radiusauthlog_username ON radius_radiusauthlog(username);
CREATE INDEX idx_radiusauthlog_status ON radius_radiusauthlog(status);
CREATE INDEX idx_radiusauthlog_created_at ON radius_radiusauthlog(created_at);

-- =============================================================================
-- Table: radius_radiusaccounting
-- Description: Comptabilité RADIUS (sessions)
-- =============================================================================
CREATE TABLE radius_radiusaccounting (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    acct_session_id         VARCHAR(255) NOT NULL,                    -- NN
    acct_unique_id          VARCHAR(255) NOT NULL UNIQUE,             -- NN, UQ
    username                VARCHAR(150) NOT NULL,                    -- NN
    nas_ip_address          INET NOT NULL,                            -- NN
    nas_port                INTEGER,
    nas_port_type           VARCHAR(50),
    acct_start_time         TIMESTAMP WITH TIME ZONE,
    acct_stop_time          TIMESTAMP WITH TIME ZONE,
    acct_session_time       INTEGER DEFAULT 0,                        -- Durée en secondes
    acct_input_octets       BIGINT DEFAULT 0,
    acct_output_octets      BIGINT DEFAULT 0,
    acct_input_packets      BIGINT DEFAULT 0,
    acct_output_packets     BIGINT DEFAULT 0,
    acct_terminate_cause    VARCHAR(100),
    framed_ip_address       INET,
    framed_protocol         VARCHAR(50),
    calling_station_id      VARCHAR(50),                              -- MAC client
    called_station_id       VARCHAR(50),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_radiusaccounting_username ON radius_radiusaccounting(username);
CREATE INDEX idx_radiusaccounting_session_id ON radius_radiusaccounting(acct_session_id);
CREATE INDEX idx_radiusaccounting_start_time ON radius_radiusaccounting(acct_start_time);

-- =============================================================================
-- Table: radius_radiusclient
-- Description: Clients RADIUS (NAS - Network Access Servers)
-- =============================================================================
CREATE TABLE radius_radiusclient (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    name                    VARCHAR(100) NOT NULL UNIQUE,             -- NN, UQ
    shortname               VARCHAR(50) NOT NULL,                     -- NN
    ip_address              INET NOT NULL UNIQUE,                     -- NN, UQ
    secret                  VARCHAR(255) NOT NULL,                    -- NN
    nas_type                VARCHAR(50) DEFAULT 'other',              -- DF
    ports                   INTEGER,
    community               VARCHAR(100),
    description             TEXT,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Table: radcheck (FreeRADIUS standard)
-- Description: Attributs de vérification par utilisateur
-- =============================================================================
CREATE TABLE radcheck (
    id                      SERIAL PRIMARY KEY,                       -- PK
    username                VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    attribute               VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    op                      VARCHAR(2) NOT NULL DEFAULT '==',         -- NN, DF (:=, ==, !=, etc.)
    value                   VARCHAR(253) NOT NULL DEFAULT '',         -- NN, DF
    statut                  BOOLEAN NOT NULL DEFAULT TRUE             -- NN, DF (extension Django)
);

CREATE INDEX idx_radcheck_username ON radcheck(username);
CREATE INDEX idx_radcheck_attribute ON radcheck(attribute);

-- =============================================================================
-- Table: radreply (FreeRADIUS standard)
-- Description: Attributs de réponse par utilisateur
-- =============================================================================
CREATE TABLE radreply (
    id                      SERIAL PRIMARY KEY,                       -- PK
    username                VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    attribute               VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    op                      VARCHAR(2) NOT NULL DEFAULT '=',          -- NN, DF
    value                   VARCHAR(253) NOT NULL DEFAULT ''          -- NN, DF
);

CREATE INDEX idx_radreply_username ON radreply(username);
CREATE INDEX idx_radreply_attribute ON radreply(attribute);

-- =============================================================================
-- Table: radgroupcheck (FreeRADIUS standard)
-- Description: Attributs de vérification par groupe
-- =============================================================================
CREATE TABLE radgroupcheck (
    id                      SERIAL PRIMARY KEY,                       -- PK
    groupname               VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    attribute               VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    op                      VARCHAR(2) NOT NULL DEFAULT '==',         -- NN, DF
    value                   VARCHAR(253) NOT NULL DEFAULT ''          -- NN, DF
);

CREATE INDEX idx_radgroupcheck_groupname ON radgroupcheck(groupname);

-- =============================================================================
-- Table: radgroupreply (FreeRADIUS standard)
-- Description: Attributs de réponse par groupe
-- =============================================================================
CREATE TABLE radgroupreply (
    id                      SERIAL PRIMARY KEY,                       -- PK
    groupname               VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    attribute               VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    op                      VARCHAR(2) NOT NULL DEFAULT '=',          -- NN, DF
    value                   VARCHAR(253) NOT NULL DEFAULT ''          -- NN, DF
);

CREATE INDEX idx_radgroupreply_groupname ON radgroupreply(groupname);

-- =============================================================================
-- Table: radusergroup (FreeRADIUS standard)
-- Description: Association utilisateur-groupe
-- =============================================================================
CREATE TABLE radusergroup (
    id                      SERIAL PRIMARY KEY,                       -- PK
    username                VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    groupname               VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    priority                INTEGER NOT NULL DEFAULT 1                -- NN, DF
);

CREATE INDEX idx_radusergroup_username ON radusergroup(username);
CREATE INDEX idx_radusergroup_groupname ON radusergroup(groupname);

-- =============================================================================
-- Table: radpostauth (FreeRADIUS standard)
-- Description: Journal post-authentification
-- =============================================================================
CREATE TABLE radpostauth (
    id                      SERIAL PRIMARY KEY,                       -- PK
    username                VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    pass                    VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    reply                   VARCHAR(32) NOT NULL DEFAULT '',          -- NN, DF
    authdate                TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW() -- NN, DF
);

CREATE INDEX idx_radpostauth_username ON radpostauth(username);
CREATE INDEX idx_radpostauth_authdate ON radpostauth(authdate);

-- =============================================================================
-- Table: radacct (FreeRADIUS standard)
-- Description: Comptabilité RADIUS complète
-- =============================================================================
CREATE TABLE radacct (
    radacctid               BIGSERIAL PRIMARY KEY,                    -- PK
    acctsessionid           VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    acctuniqueid            VARCHAR(32) NOT NULL UNIQUE,              -- NN, UQ
    username                VARCHAR(64) NOT NULL DEFAULT '',          -- NN, DF
    realm                   VARCHAR(64) DEFAULT '',
    nasipaddress            VARCHAR(15) NOT NULL DEFAULT '',          -- NN, DF
    nasportid               VARCHAR(15),
    nasporttype             VARCHAR(32),
    acctstarttime           TIMESTAMP WITH TIME ZONE,
    acctupdatetime          TIMESTAMP WITH TIME ZONE,
    acctstoptime            TIMESTAMP WITH TIME ZONE,
    acctinterval            INTEGER,
    acctsessiontime         INTEGER,
    acctauthentic           VARCHAR(32),
    connectinfo_start       VARCHAR(50),
    connectinfo_stop        VARCHAR(50),
    acctinputoctets         BIGINT,
    acctoutputoctets        BIGINT,
    calledstationid         VARCHAR(50) NOT NULL DEFAULT '',          -- NN, DF
    callingstationid        VARCHAR(50) NOT NULL DEFAULT '',          -- NN, DF (MAC client)
    acctterminatecause      VARCHAR(32) NOT NULL DEFAULT '',          -- NN, DF
    servicetype             VARCHAR(32),
    framedprotocol          VARCHAR(32),
    framedipaddress         VARCHAR(15) NOT NULL DEFAULT '',          -- NN, DF
    framedipv6address       VARCHAR(45) NOT NULL DEFAULT '',          -- NN, DF
    framedipv6prefix        VARCHAR(45) NOT NULL DEFAULT '',          -- NN, DF
    framedinterfaceid       VARCHAR(44) NOT NULL DEFAULT '',          -- NN, DF
    delegatedipv6prefix     VARCHAR(45) NOT NULL DEFAULT ''           -- NN, DF
);

CREATE INDEX idx_radacct_username ON radacct(username);
CREATE INDEX idx_radacct_acctsessionid ON radacct(acctsessionid);
CREATE INDEX idx_radacct_acctstarttime ON radacct(acctstarttime);
CREATE INDEX idx_radacct_acctstoptime ON radacct(acctstoptime);
CREATE INDEX idx_radacct_nasipaddress ON radacct(nasipaddress);
CREATE INDEX idx_radacct_callingstationid ON radacct(callingstationid);


-- #############################################################################
-- APPLICATION MIKROTIK - Tables de gestion MikroTik
-- #############################################################################

-- =============================================================================
-- Table: mikrotik_mikrotikrouter
-- Description: Configuration des routeurs MikroTik
-- =============================================================================
CREATE TABLE mikrotik_mikrotikrouter (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    name                    VARCHAR(100) NOT NULL UNIQUE,             -- NN, UQ
    host                    VARCHAR(255) NOT NULL,                    -- NN
    port                    INTEGER NOT NULL DEFAULT 8728,            -- NN, DF (API port)
    username                VARCHAR(100) NOT NULL,                    -- NN
    password                VARCHAR(255) NOT NULL,                    -- NN (chiffré)
    use_ssl                 BOOLEAN NOT NULL DEFAULT FALSE,           -- NN, DF
    is_primary              BOOLEAN NOT NULL DEFAULT FALSE,           -- NN, DF
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,            -- NN, DF
    last_sync               TIMESTAMP WITH TIME ZONE,
    last_error              TEXT,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Table: mikrotik_mikrotikhotspotuser
-- Description: Utilisateurs hotspot synchronisés vers MikroTik
-- =============================================================================
CREATE TABLE mikrotik_mikrotikhotspotuser (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    router_id               BIGINT NOT NULL REFERENCES mikrotik_mikrotikrouter(id) -- FK
                            ON DELETE CASCADE,
    user_id                 BIGINT REFERENCES core_user(id)           -- FK → core_user
                            ON DELETE SET NULL,
    mikrotik_id             VARCHAR(100),                             -- ID interne MikroTik (.id)
    username                VARCHAR(150) NOT NULL,                    -- NN
    password                VARCHAR(255),
    profile                 VARCHAR(100),                             -- Profil hotspot MikroTik
    mac_address             VARCHAR(17),
    limit_uptime            VARCHAR(50),
    limit_bytes_total       BIGINT,
    is_disabled             BOOLEAN NOT NULL DEFAULT FALSE,           -- NN, DF
    comment                 TEXT,
    sync_status             VARCHAR(20) NOT NULL DEFAULT 'pending',   -- NN, DF
    last_sync               TIMESTAMP WITH TIME ZONE,
    last_error              TEXT,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_hotspotuser_router_username UNIQUE(router_id, username)
);

CREATE INDEX idx_mikrotikhotspotuser_router_id ON mikrotik_mikrotikhotspotuser(router_id);
CREATE INDEX idx_mikrotikhotspotuser_user_id ON mikrotik_mikrotikhotspotuser(user_id);
CREATE INDEX idx_mikrotikhotspotuser_username ON mikrotik_mikrotikhotspotuser(username);
CREATE INDEX idx_mikrotikhotspotuser_sync_status ON mikrotik_mikrotikhotspotuser(sync_status);

-- =============================================================================
-- Table: mikrotik_mikrotikactiveconnection
-- Description: Connexions actives sur le hotspot MikroTik
-- =============================================================================
CREATE TABLE mikrotik_mikrotikactiveconnection (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    router_id               BIGINT NOT NULL REFERENCES mikrotik_mikrotikrouter(id) -- FK
                            ON DELETE CASCADE,
    user_id                 BIGINT REFERENCES core_user(id)           -- FK → core_user
                            ON DELETE SET NULL,
    mikrotik_id             VARCHAR(100),                             -- ID interne MikroTik
    username                VARCHAR(150) NOT NULL,                    -- NN
    address                 INET,
    mac_address             VARCHAR(17),
    uptime                  VARCHAR(50),
    idle_time               VARCHAR(50),
    bytes_in                BIGINT DEFAULT 0,
    bytes_out               BIGINT DEFAULT 0,
    packets_in              BIGINT DEFAULT 0,
    packets_out             BIGINT DEFAULT 0,
    login_by                VARCHAR(50),
    session_id              VARCHAR(255),
    detected_at             TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mikrotikactiveconnection_router_id ON mikrotik_mikrotikactiveconnection(router_id);
CREATE INDEX idx_mikrotikactiveconnection_user_id ON mikrotik_mikrotikactiveconnection(user_id);
CREATE INDEX idx_mikrotikactiveconnection_username ON mikrotik_mikrotikactiveconnection(username);

-- =============================================================================
-- Table: mikrotik_mikrotiklog
-- Description: Journal des opérations MikroTik
-- =============================================================================
CREATE TABLE mikrotik_mikrotiklog (
    id                      BIGSERIAL PRIMARY KEY,                    -- PK
    router_id               BIGINT REFERENCES mikrotik_mikrotikrouter(id) -- FK
                            ON DELETE SET NULL,
    operation               VARCHAR(100) NOT NULL,                    -- NN (create_user, update_user, delete_user, sync, etc.)
    target_type             VARCHAR(50),                              -- Type cible (user, profile, firewall, etc.)
    target_id               VARCHAR(100),
    target_repr             VARCHAR(255),
    status                  VARCHAR(20) NOT NULL,                     -- NN (success, error, pending)
    details                 JSONB,
    error_message           TEXT,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mikrotiklog_router_id ON mikrotik_mikrotiklog(router_id);
CREATE INDEX idx_mikrotiklog_operation ON mikrotik_mikrotiklog(operation);
CREATE INDEX idx_mikrotiklog_status ON mikrotik_mikrotiklog(status);
CREATE INDEX idx_mikrotiklog_created_at ON mikrotik_mikrotiklog(created_at);


-- #############################################################################
-- RELATIONS ET CONTRAINTES ADDITIONNELLES
-- #############################################################################

-- Commentaires sur les tables principales
COMMENT ON TABLE core_profile IS 'Profils de connexion définissant quotas, bande passante et restrictions';
COMMENT ON TABLE core_promotion IS 'Groupes d''utilisateurs partageant les mêmes droits (classes, départements)';
COMMENT ON TABLE core_user IS 'Utilisateurs du portail captif avec intégration RADIUS';
COMMENT ON TABLE core_blockedsite IS 'Sites bloqués par profil, promotion ou globalement';
COMMENT ON TABLE core_syncfailurelog IS 'Journal des échecs de synchronisation avec mécanisme de retry';

COMMENT ON TABLE radcheck IS 'Table FreeRADIUS: attributs de vérification utilisateur (mot de passe)';
COMMENT ON TABLE radreply IS 'Table FreeRADIUS: attributs de réponse (Session-Timeout, Rate-Limit)';
COMMENT ON TABLE radusergroup IS 'Table FreeRADIUS: association utilisateur-groupe pour profils';
COMMENT ON TABLE radgroupreply IS 'Table FreeRADIUS: attributs de réponse par groupe/profil';
COMMENT ON TABLE radacct IS 'Table FreeRADIUS: comptabilité des sessions';

COMMENT ON TABLE mikrotik_mikrotikhotspotuser IS 'Utilisateurs hotspot synchronisés vers MikroTik';
COMMENT ON TABLE mikrotik_mikrotikactiveconnection IS 'Connexions actives détectées sur MikroTik';


-- #############################################################################
-- DIAGRAMME RELATIONNEL (ASCII)
-- #############################################################################
/*
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SCHÉMA RELATIONNEL SIMPLIFIÉ                         │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │ core_profile │
                              ├──────────────┤
                              │ PK: id       │
                              │ bandwidth    │
                              │ quotas       │
                              │ restrictions │
                              └──────┬───────┘
                                     │ 1:N
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│ core_promotion  │         │   core_user     │         │ core_blockedsite│
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ PK: id          │◄───────►│ PK: id          │         │ PK: id          │
│ FK: profile_id  │  N:1    │ FK: profile_id  │         │ FK: profile_id  │
└────────┬────────┘         │ FK: promotion_id│         │ FK: promotion_id│
         │                  │ cleartext_pass  │         └─────────────────┘
         │                  │ is_radius_activ │
         │                  └────────┬────────┘
         │                           │
         │              ┌────────────┴────────────┐
         │              │                         │
         │              ▼                         ▼
         │     ┌─────────────────┐       ┌─────────────────┐
         │     │  core_device    │       │  core_session   │
         │     ├─────────────────┤       ├─────────────────┤
         │     │ PK: id          │       │ PK: id          │
         │     │ FK: user_id     │       │ FK: user_id     │
         │     │ mac_address     │       │ FK: device_id   │
         │     └─────────────────┘       │ session_id      │
         │                               └─────────────────┘
         │
         └──────────────────────────────────────────────────────┐
                                                                │
┌───────────────────────────────────────────────────────────────┴─────────────┐
│                              RADIUS (FreeRADIUS)                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │   radcheck   │    │   radreply   │    │ radusergroup │    │ radgroupre │ │
│  ├──────────────┤    ├──────────────┤    ├──────────────┤    ├────────────┤ │
│  │ username ────┼────┼─► username ◄─┼────┼─ username    │    │ groupname  │ │
│  │ Cleartext-   │    │ Session-     │    │ groupname ───┼────┼─►          │ │
│  │ Password     │    │ Timeout      │    │ priority     │    │ Mikrotik-  │ │
│  │ statut       │    │ Mikrotik-    │    └──────────────┘    │ Rate-Limit │ │
│  └──────────────┘    │ Rate-Limit   │                        └────────────┘ │
│                      └──────────────┘                                        │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐                                        │
│  │  radpostauth │    │    radacct   │                                        │
│  ├──────────────┤    ├──────────────┤                                        │
│  │ username     │    │ username     │                                        │
│  │ reply        │    │ session data │                                        │
│  │ authdate     │    │ accounting   │                                        │
│  └──────────────┘    └──────────────┘                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                              MIKROTIK                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐                                                      │
│  │ mikrotik_router    │                                                      │
│  ├────────────────────┤                                                      │
│  │ PK: id             │                                                      │
│  │ host, credentials  │                                                      │
│  └─────────┬──────────┘                                                      │
│            │ 1:N                                                             │
│    ┌───────┴────────┬──────────────────┐                                     │
│    ▼                ▼                  ▼                                     │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                           │
│ │ hotspot_user │ │active_connec │ │ mikrotik_log │                           │
│ ├──────────────┤ ├──────────────┤ ├──────────────┤                           │
│ │FK: router_id │ │FK: router_id │ │FK: router_id │                           │
│ │FK: user_id   │ │FK: user_id   │ │ operation    │                           │
│ │ sync_status  │ │ session_data │ │ status       │                           │
│ └──────────────┘ └──────────────┘ └──────────────┘                           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

FLUX DE SYNCHRONISATION:
========================

1. Création/Modification User (Django)
   │
   ├──► Signal post_save
   │
   ├──► Sync vers radcheck (mot de passe)
   │    Sync vers radreply (Session-Timeout, Rate-Limit)
   │    Sync vers radusergroup (association profil)
   │
   └──► Si échec: SyncFailureLog + retry automatique

2. Authentification User (MikroTik → FreeRADIUS)
   │
   ├──► FreeRADIUS vérifie radcheck
   ├──► FreeRADIUS retourne radreply + radgroupreply
   │
   └──► MikroTik applique les attributs (bande passante, timeout)

3. Session Accounting (MikroTik → FreeRADIUS)
   │
   ├──► Start/Interim/Stop → radacct
   │
   └──► Django synchronise core_session + core_userquota

*/
