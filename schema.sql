-- =============================================================================
-- Vigilant — Production-Ready MySQL Schema
-- Subscription Lifecycle Management System
--
-- Run with:  mysql -u root -p < schema.sql
-- =============================================================================

CREATE DATABASE IF NOT EXISTS vigilant_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE vigilant_db;

-- ─────────────────────────────────────────────────────────────────────────────
-- Users
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              VARCHAR(36)     NOT NULL,
    email           VARCHAR(255)    NOT NULL,
    username        VARCHAR(100)    NOT NULL,
    hashed_password TEXT            NULL,           -- NULL for OAuth-only users
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    is_oauth_user   BOOLEAN         NOT NULL DEFAULT FALSE,
    oauth_provider  VARCHAR(50)     NULL,
    avatar_url      VARCHAR(512)    NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE  KEY uq_users_email    (email),
    UNIQUE  KEY uq_users_username (username),
    INDEX   ix_users_email        (email),
    INDEX   ix_users_username     (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- Subscriptions
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subscriptions (
    id              VARCHAR(36)     NOT NULL,
    owner_id        VARCHAR(36)     NOT NULL,
    service_name    VARCHAR(200)    NOT NULL,
    service_url     VARCHAR(512)    NULL,
    cost_per_cycle  DECIMAL(10, 2)  NULL,
    billing_cycle   VARCHAR(50)     NULL,
    trial_start_date DATE           NOT NULL,
    trial_end_date  DATE            NOT NULL,
    status          ENUM('active', 'expiring', 'notified', 'expired', 'cancelled')
                                    NOT NULL DEFAULT 'active',
    notes           TEXT            NULL,
    cancel_url      VARCHAR(512)    NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    -- Foreign key with cascading delete
    CONSTRAINT fk_sub_owner
        FOREIGN KEY (owner_id) REFERENCES users(id)
        ON DELETE CASCADE,

    -- Performance indexes for the Watcher's hot queries
    INDEX ix_sub_owner_id       (owner_id),
    INDEX ix_sub_trial_end      (trial_end_date),
    INDEX ix_sub_status         (status),
    INDEX ix_sub_owner_status   (owner_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- Notifications
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id                VARCHAR(36)     NOT NULL,
    user_id           VARCHAR(36)     NOT NULL,
    subscription_id   VARCHAR(36)     NOT NULL,
    notification_type ENUM('email', 'in_app', 'sms')
                                      NOT NULL DEFAULT 'in_app',
    message           TEXT            NOT NULL,
    sent_at           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    CONSTRAINT fk_notif_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_notif_sub
        FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
        ON DELETE CASCADE,

    INDEX ix_notif_user_id  (user_id),
    INDEX ix_notif_sub_id   (subscription_id),
    INDEX ix_notif_sent_at  (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- Optional: Create a dedicated application user with limited privileges
-- ─────────────────────────────────────────────────────────────────────────────
-- CREATE USER IF NOT EXISTS 'vigilant_user'@'%' IDENTIFIED BY 'vigilant_pass';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON vigilant_db.* TO 'vigilant_user'@'%';
-- FLUSH PRIVILEGES;
