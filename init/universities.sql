-- init.sql: seed 10 universities, 10 programs и 10 scholarships

BEGIN;

-- 1) Университеты (10 записей)
INSERT INTO universities_university (id, name, country, city, description, study_format)
VALUES
  (1,  'Alpha University',     'Aland',     'CityA', 'Leading online university in Aland.',          'online'),
  (2,  'Beta Institute',       'Betaland',  'CityB', 'Campus-based research institute.',               'campus'),
  (3,  'Gamma College',        'Gammaland', 'CityC', 'Hybrid learning with strong research focus.',    'hybrid'),
  (4,  'Delta Technical',      'Deltaville','CityD', 'Technical university specializing in engineering.','campus'),
  (5,  'Epsilon Academy',      'Epsilonia','CityE', 'Online academy for liberal arts and sciences.',    'online'),
  (6,  'Zeta School',          'Zetania',   'CityF', 'Small on-campus school with personalized teaching.','campus'),
  (7,  'Eta University',       'Etaland',   'CityG', 'Hybrid model university with global partnerships.','hybrid'),
  (8,  'Theta Institute',      'Thetania',  'CityH', 'Science-focused institute offering modern labs.',  'campus'),
  (9,  'Iota College',         'Iotaland',  'CityI', 'Online college with extensive distance programs.', 'online'),
  (10, 'Kappa College',        'Kappaland','CityJ', 'Hybrid arts and business college.',               'hybrid');

-- 2) Программы (10 записей)
INSERT INTO universities_program (
  id, university_id, name, study_type, study_format,
  city, country, tuition_fee, duration, rating, deadline
)
VALUES
  (1,  1,  'Alpha Bachelor of Science',     'full-time', 'online',  'CityA', 'Aland',     8000, '4 years', 4.2, '2025-06-22'),
  (2,  2,  'Beta Master of Arts',           'part-time', 'campus',  'CityB', 'Betaland',  6000, '2 years', 4.5, '2025-07-07'),
  (3,  3,  'Gamma MBA',                     'full-time', 'hybrid',  'CityC', 'Gammaland', 12000,'1 year',  4.0, '2025-08-15'),
  (4,  4,  'Delta B.Eng in Mechanical Eng.', 'full-time', 'campus', 'CityD', 'Deltaville',9000, '4 years', 3.9, '2025-09-10'),
  (5,  5,  'Epsilon BA in English',         'part-time', 'online',  'CityE', 'Epsilonia', 7000, '3 years', 4.3, '2025-10-01'),
  (6,  6,  'Zeta Certificate in IT',        'part-time', 'campus',  'CityF', 'Zetania',   3000, '6 months',3.7, '2025-11-20'),
  (7,  7,  'Eta PhD in Physics',            'full-time', 'hybrid',  'CityG', 'Etaland',  15000,'5 years', 4.8, '2025-12-05'),
  (8,  8,  'Theta MSc in Chemistry',        'full-time', 'campus',  'CityH', 'Thetania', 11000,'2 years', 4.1, '2025-12-20'),
  (9,  9,  'Iota Diploma in Media Studies', 'part-time', 'online',  'CityI', 'Iotaland',  5000, '1 year',  3.8, '2026-01-15'),
  (10, 10, 'Kappa Diploma in Arts',         'part-time', 'hybrid',  'CityJ', 'Kappaland', 6500, '1 year',  3.8, '2025-12-15');

-- 3) Стипендии (10 записей)
INSERT INTO universities_scholarship (
  id, name, country, amount, currency,
  deadline, result_date, description,
  min_ielts, min_toefl, min_sat, min_act
)
VALUES
  (1,  'Aland Excellence',           'Aland',    5000, 'USD', '2025-06-30', '2025-07-30',
        'Merit-based scholarship for top students.',   '7.0',  '90',   NULL,   NULL),
  (2,  'Betaland Research Grant',    'Betaland', 3000, 'USD', '2025-07-02', NULL,
        'Support for research assistants.',            NULL,   NULL,   '1200', '25'),
  (3,  'Gamma Global Fellowship',    'Gammaland',8000, 'USD', '2025-08-01', '2025-09-01',
        'Fellowship for outstanding global researchers.','7.5', '95',   NULL,   NULL),
  (4,  'Delta Engineering Award',    'Deltaville',4000,'USD', '2025-09-15', NULL,
        'Award for engineering innovation.',          NULL,   NULL,   '1100', NULL),
  (5,  'Epsilon Arts Scholarship',   'Epsilonia',4500, 'USD', '2025-10-05', '2025-11-05',
        'Scholarship for liberal arts excellence.',  '6.5',  NULL,   NULL,   NULL),
  (6,  'Zeta Tech Grant',            'Zetania',   3500, 'USD', '2025-11-30', NULL,
        'Grant for IT and computing projects.',      NULL,   '85',   NULL,   NULL),
  (7,  'Eta Physics Fellowship',     'Etaland',   9000, 'USD', '2025-12-10', '2026-01-10',
        'Fellowship for PhD physics candidates.',    '7.0',  NULL,   NULL,   NULL),
  (8,  'Theta Chemistry Award',      'Thetania',  7500, 'USD', '2025-12-25', NULL,
        'Award for excellence in chemistry research.','7.2',  '88',   NULL,   NULL),
  (9,  'Iota Media Scholarship',     'Iotaland',  2800, 'USD', '2026-01-20', NULL,
        'Support for media and communications studies.',NULL,NULL,   NULL,   '23'),
  (10, 'Kappa Future Leaders',       'Kappaland',4500, 'USD', '2025-09-30', NULL,
        'Scholarship for emerging global leaders.',  NULL,   '85',   '1150','24');

COMMIT;
