CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    department_id INTEGER NOT NULL,
    position_id INTEGER NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (position_id) REFERENCES positions(id)
);

CREATE TABLE IF NOT EXISTS statuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL, -- NEW, IN_PROGRESS, DONE
    name TEXT UNIQUE NOT NULL  -- Новая, В работе, Выполнена
);

CREATE TABLE IF NOT EXISTS status_transitions (
    from_status_id INTEGER NOT NULL,
    to_status_id INTEGER NOT NULL,
    PRIMARY KEY (from_status_id, to_status_id),
    FOREIGN KEY (from_status_id) REFERENCES statuses(id),
    FOREIGN KEY (to_status_id) REFERENCES statuses(id)
);

CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    author_id INTEGER NOT NULL,
    executor_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    due_date DATE NOT NULL,
    status_id INTEGER NOT NULL,
    FOREIGN KEY (author_id) REFERENCES employees(id),
    FOREIGN KEY (executor_id) REFERENCES employees(id),
    FOREIGN KEY (status_id) REFERENCES statuses(id)
);

CREATE INDEX IF NOT EXISTS idx_requests_executor_status_due_date ON requests(executor_id, status_id, due_date);
CREATE INDEX IF NOT EXISTS idx_requests_status_id ON requests(status_id);
CREATE INDEX IF NOT EXISTS idx_requests_executor_id ON requests(executor_id);
CREATE INDEX IF NOT EXISTS idx_requests_due_date ON requests(due_date);
