-- 1. Пользователи и аутентификация

CREATE TABLE users (
    id                SERIAL PRIMARY KEY,
    email             VARCHAR(255) UNIQUE NOT NULL,
    password_hash     TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE user_profiles (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    avatar_url      TEXT,
    bio             TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE oauth_accounts (
    id                  SERIAL PRIMARY KEY,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider            VARCHAR(50) NOT NULL,         -- 'google', 'apple', 'facebook', 'microsoft'
    provider_user_id    VARCHAR(255) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, provider, provider_user_id)
);

CREATE TABLE user_roles (
    id        SERIAL PRIMARY KEY,
    name      VARCHAR(50) UNIQUE NOT NULL,           -- 'admin', 'user', 'moderator', ...
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE user_role_assignments (
    id        SERIAL PRIMARY KEY,
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id   INTEGER NOT NULL REFERENCES user_roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, role_id)
);


-- 2. Университеты и поиск

CREATE TABLE universities (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(255) NOT NULL,
    country      VARCHAR(100),
    city         VARCHAR(100),
    website      VARCHAR(255),
    logo_url     TEXT,
    description  TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE programs (
    id               SERIAL PRIMARY KEY,
    university_id    INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    name             VARCHAR(255) NOT NULL,
    degree_level     VARCHAR(100),      -- 'Bachelor', 'Master', 'PhD', ...
    duration         VARCHAR(50),       -- e.g. '2 years'
    description      TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE favorites (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    university_id  INTEGER REFERENCES universities(id) ON DELETE CASCADE,
    program_id     INTEGER REFERENCES programs(id) ON DELETE CASCADE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
      (university_id IS NOT NULL AND program_id IS NULL)
      OR (program_id IS NOT NULL)
    )
);


-- 3. Подписки и платежи

CREATE TABLE plans (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    price       NUMERIC(10,2) NOT NULL,
    interval    VARCHAR(20) NOT NULL,    -- 'monthly', 'yearly'
    features    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE subscriptions (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id       INTEGER NOT NULL REFERENCES plans(id),
    start_date    DATE NOT NULL,
    end_date      DATE,
    status        VARCHAR(20) NOT NULL,  -- 'active', 'canceled', 'past_due', ...
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE payments (
    id                SERIAL PRIMARY KEY,
    subscription_id   INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    amount            NUMERIC(10,2) NOT NULL,
    currency          VARCHAR(3) NOT NULL,           -- 'USD', 'KZT', ...
    payment_provider  VARCHAR(50) NOT NULL,          -- 'stripe', 'kaspi_qr', ...
    status            VARCHAR(20) NOT NULL,          -- 'succeeded', 'failed', ...
    paid_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- 4. Onboarding и вопросы

CREATE TABLE onboarding_questions (
    id         SERIAL PRIMARY KEY,
    text       TEXT NOT NULL,
    "order"    INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE onboarding_responses (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id   INTEGER NOT NULL REFERENCES onboarding_questions(id) ON DELETE CASCADE,
    answer        TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, question_id)
);


-- 5. AI-сервисы: письма и CV

CREATE TABLE letters (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject     TEXT,
    body        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE letter_revisions (
    id               SERIAL PRIMARY KEY,
    letter_id        INTEGER NOT NULL REFERENCES letters(id) ON DELETE CASCADE,
    revision_number  INTEGER NOT NULL,
    body             TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(letter_id, revision_number)
);

CREATE TABLE cvs (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    data        JSONB NOT NULL,       -- структура CV
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE cv_revisions (
    id               SERIAL PRIMARY KEY,
    cv_id            INTEGER NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
    revision_number  INTEGER NOT NULL,
    data             JSONB NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(cv_id, revision_number)
);


-- 6. Профориентационные тесты

CREATE TABLE career_tests (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE test_questions (
    id             SERIAL PRIMARY KEY,
    test_id        INTEGER NOT NULL REFERENCES career_tests(id) ON DELETE CASCADE,
    question_text  TEXT NOT NULL,
    question_type  VARCHAR(50) NOT NULL,   -- 'single_choice', 'multiple_choice', 'scale', ...
    metadata       JSONB,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE test_results (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    test_id     INTEGER NOT NULL REFERENCES career_tests(id) ON DELETE CASCADE,
    score       NUMERIC(5,2),
    taken_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, test_id)
);


-- 7. Учёт расходов

CREATE TABLE expense_categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    icon        VARCHAR(255),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE expenses (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id     INTEGER NOT NULL REFERENCES expense_categories(id),
    amount          NUMERIC(12,2) NOT NULL,
    currency        VARCHAR(3) NOT NULL,
    date            DATE NOT NULL,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- 8. Логи AI-запросов и аналитика

CREATE TABLE ai_requests (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER REFERENCES users(id) ON DELETE SET NULL,
    service           VARCHAR(50) NOT NULL,     -- 'letter', 'cv', ...
    request_payload   JSONB NOT NULL,
    response_payload  JSONB NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- 9. Вспомогательные страницы

CREATE TABLE faqs (
    id         SERIAL PRIMARY KEY,
    question   TEXT NOT NULL,
    answer     TEXT NOT NULL,
    "order"    INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE pages (
    id          SERIAL PRIMARY KEY,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    title       VARCHAR(255) NOT NULL,
    content     TEXT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
