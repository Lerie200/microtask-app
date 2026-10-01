-- ============================================
-- Microtask App Schema (practice project)
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_activated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,       -- e.g. 'photo', 'voice_reading', 'conversation'
    title VARCHAR(150) NOT NULL,
    instructions TEXT NOT NULL,
    reward_amount NUMERIC(6,2) NOT NULL,  -- KSh per completed task
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    file_url VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending / approved / rejected
    submitted_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount NUMERIC(6,2) NOT NULL,
    mpesa_receipt VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending / success / failed
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================
-- Seed data: guessed per-task rates (KSh)
-- ============================================
INSERT INTO tasks (task_type, title, instructions, reward_amount) VALUES
('photo',          'Take a specific photo',        'Take a clear photo of the object/receipt/sign shown in the example.', 10.00),
('voice_reading',  'Record yourself reading',       'Read the given sentence aloud clearly and record it.',                15.00),
('conversation',   'Record a short conversation',   'Record a short everyday conversation as instructed.',                 20.00),
('audio_choice',   'Listen and choose',             'Listen to the short audio clip and select what you hear.',             5.00),
('image_choice',   'Select the matching picture',   'Look at the pictures and select the one that matches.',                5.00),
('count_objects',  'Count objects in a photo',      'Count how many objects appear in the given photo.',                    8.00),
('categorize',     'Categorize the picture',        'Place the picture into the correct simple category.',                  8.00),
('rate_picture',   'Rate the picture',              'Rate the picture as good/bad or relevant/not relevant.',               5.00),
('compare_images', 'Compare two pictures',          'Compare the two pictures and identify the differences.',              10.00)
ON CONFLICT DO NOTHING;
