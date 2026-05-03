-- Deep Training For TOEIC
-- Script unique Supabase/Postgres
-- A rejouer et enrichir au fil du projet.

create extension if not exists "pgcrypto";

create schema if not exists app;

create or replace function app.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table if not exists app.profiles (
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid unique,
  role text not null default 'adherent' check (role in ('adherent', 'admin', 'coach')),
  full_name text not null,
  avatar text not null default 'AS',
  current_step integer not null default 1 check (current_step between 1 and 5),
  current_step_label text not null default 'Etape 1',
  deadline_label text not null default '',
  target_score integer not null default 785 check (target_score between 10 and 990),
  start_score integer not null default 0 check (start_score between 0 and 990),
  current_score integer not null default 0 check (current_score between 0 and 990),
  listening_score integer not null default 0 check (listening_score between 0 and 495),
  reading_score integer not null default 0 check (reading_score between 0 and 495),
  regularity_percent integer not null default 0 check (regularity_percent between 0 and 100),
  regularity_label text not null default '',
  risk_primary text not null default '',
  risk_detail text not null default '',
  weak_zones text not null default '',
  coach_tip text not null default '',
  is_active boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.program_steps (
  id uuid primary key default gen_random_uuid(),
  step_number integer not null unique check (step_number between 1 and 5),
  name text not null,
  description text not null default '',
  status_label text not null default 'Verrouillee',
  status_tone text not null default '',
  progress_percent integer check (progress_percent between 0 and 100),
  progress_detail text not null default '',
  is_active boolean not null default false,
  is_locked boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.program_step_items (
  id uuid primary key default gen_random_uuid(),
  step_id uuid not null references app.program_steps(id) on delete cascade,
  label text not null,
  color text not null default 'var(--accent)',
  sort_order integer not null default 0,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.score_entries (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references app.profiles(id) on delete cascade,
  taken_on date not null default current_date,
  listening integer not null check (listening between 0 and 495),
  reading integer not null check (reading between 0 and 495),
  total integer generated always as (listening + reading) stored,
  format_label text not null,
  is_current boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.score_analysis (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references app.profiles(id) on delete cascade,
  part_label text not null,
  percent integer not null check (percent between 0 and 100),
  level_label text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.notes (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references app.profiles(id) on delete cascade,
  title text not null,
  meta text not null default '',
  step_label text not null default '',
  content text not null default '',
  tag text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.note_words (
  id uuid primary key default gen_random_uuid(),
  note_id uuid not null references app.notes(id) on delete cascade,
  word text not null,
  state text not null default '' check (state in ('', 'review', 'mastered')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.resources (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  meta text not null default '',
  category text not null default '',
  icon text not null default 'RS',
  tone_class text not null default '',
  is_locked boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.resource_statuses (
  id uuid primary key default gen_random_uuid(),
  resource_id uuid not null references app.resources(id) on delete cascade,
  label text not null,
  tone text not null default '',
  sort_order integer not null default 0,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.support_messages (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references app.profiles(id) on delete cascade,
  sender_name text not null,
  sender_avatar text not null default 'AS',
  sent_at timestamptz not null default timezone('utc', now()),
  is_read boolean not null default false,
  content text not null,
  border_color text not null default '#22d3ff',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.chat_messages (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references app.profiles(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  sent_at timestamptz not null default timezone('utc', now()),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.activity_entries (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references app.profiles(id) on delete cascade,
  happened_at timestamptz not null default timezone('utc', now()),
  action_label text not null,
  type_label text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.daily_missions (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references app.profiles(id) on delete cascade,
  mission_number text not null,
  title text not null,
  subtitle text not null,
  priority text not null check (priority in ('info', 'warn', 'urgent')),
  sort_order integer not null default 0,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

alter table app.profiles enable row level security;
alter table app.program_steps enable row level security;
alter table app.program_step_items enable row level security;
alter table app.score_entries enable row level security;
alter table app.score_analysis enable row level security;
alter table app.notes enable row level security;
alter table app.note_words enable row level security;
alter table app.resources enable row level security;
alter table app.resource_statuses enable row level security;
alter table app.support_messages enable row level security;
alter table app.chat_messages enable row level security;
alter table app.activity_entries enable row level security;
alter table app.daily_missions enable row level security;

drop policy if exists "profiles_select_own" on app.profiles;
create policy "profiles_select_own" on app.profiles
for select using (auth.uid() = auth_user_id);

drop policy if exists "profiles_update_own" on app.profiles;
create policy "profiles_update_own" on app.profiles
for update using (auth.uid() = auth_user_id);

drop policy if exists "program_steps_read_all_auth" on app.program_steps;
create policy "program_steps_read_all_auth" on app.program_steps
for select using (auth.role() = 'authenticated');

drop policy if exists "program_step_items_read_all_auth" on app.program_step_items;
create policy "program_step_items_read_all_auth" on app.program_step_items
for select using (auth.role() = 'authenticated');

drop policy if exists "resources_read_all_auth" on app.resources;
create policy "resources_read_all_auth" on app.resources
for select using (auth.role() = 'authenticated');

drop policy if exists "resource_statuses_read_all_auth" on app.resource_statuses;
create policy "resource_statuses_read_all_auth" on app.resource_statuses
for select using (auth.role() = 'authenticated');

drop policy if exists "score_entries_crud_own" on app.score_entries;
create policy "score_entries_crud_own" on app.score_entries
for all using (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
);

drop policy if exists "score_analysis_crud_own" on app.score_analysis;
create policy "score_analysis_crud_own" on app.score_analysis
for all using (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
);

drop policy if exists "notes_crud_own" on app.notes;
create policy "notes_crud_own" on app.notes
for all using (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
);

drop policy if exists "note_words_crud_via_note_owner" on app.note_words;
create policy "note_words_crud_via_note_owner" on app.note_words
for all using (
  exists (
    select 1
    from app.notes n
    join app.profiles p on p.id = n.profile_id
    where n.id = note_id and p.auth_user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from app.notes n
    join app.profiles p on p.id = n.profile_id
    where n.id = note_id and p.auth_user_id = auth.uid()
  )
);

drop policy if exists "support_messages_crud_own" on app.support_messages;
create policy "support_messages_crud_own" on app.support_messages
for all using (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
);

drop policy if exists "chat_messages_crud_own" on app.chat_messages;
create policy "chat_messages_crud_own" on app.chat_messages
for all using (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
);

drop policy if exists "activity_entries_crud_own" on app.activity_entries;
create policy "activity_entries_crud_own" on app.activity_entries
for all using (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
);

drop policy if exists "daily_missions_crud_own" on app.daily_missions;
create policy "daily_missions_crud_own" on app.daily_missions
for all using (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from app.profiles p
    where p.id = profile_id and p.auth_user_id = auth.uid()
  )
);

drop trigger if exists trg_profiles_updated_at on app.profiles;
create trigger trg_profiles_updated_at before update on app.profiles
for each row execute function app.set_updated_at();

drop trigger if exists trg_program_steps_updated_at on app.program_steps;
create trigger trg_program_steps_updated_at before update on app.program_steps
for each row execute function app.set_updated_at();

drop trigger if exists trg_program_step_items_updated_at on app.program_step_items;
create trigger trg_program_step_items_updated_at before update on app.program_step_items
for each row execute function app.set_updated_at();

drop trigger if exists trg_score_entries_updated_at on app.score_entries;
create trigger trg_score_entries_updated_at before update on app.score_entries
for each row execute function app.set_updated_at();

drop trigger if exists trg_score_analysis_updated_at on app.score_analysis;
create trigger trg_score_analysis_updated_at before update on app.score_analysis
for each row execute function app.set_updated_at();

drop trigger if exists trg_notes_updated_at on app.notes;
create trigger trg_notes_updated_at before update on app.notes
for each row execute function app.set_updated_at();

drop trigger if exists trg_note_words_updated_at on app.note_words;
create trigger trg_note_words_updated_at before update on app.note_words
for each row execute function app.set_updated_at();

drop trigger if exists trg_resources_updated_at on app.resources;
create trigger trg_resources_updated_at before update on app.resources
for each row execute function app.set_updated_at();

drop trigger if exists trg_resource_statuses_updated_at on app.resource_statuses;
create trigger trg_resource_statuses_updated_at before update on app.resource_statuses
for each row execute function app.set_updated_at();

drop trigger if exists trg_support_messages_updated_at on app.support_messages;
create trigger trg_support_messages_updated_at before update on app.support_messages
for each row execute function app.set_updated_at();

drop trigger if exists trg_chat_messages_updated_at on app.chat_messages;
create trigger trg_chat_messages_updated_at before update on app.chat_messages
for each row execute function app.set_updated_at();

drop trigger if exists trg_activity_entries_updated_at on app.activity_entries;
create trigger trg_activity_entries_updated_at before update on app.activity_entries
for each row execute function app.set_updated_at();

drop trigger if exists trg_daily_missions_updated_at on app.daily_missions;
create trigger trg_daily_missions_updated_at before update on app.daily_missions
for each row execute function app.set_updated_at();

insert into app.profiles (
  id,
  auth_user_id,
  role,
  full_name,
  avatar,
  current_step,
  current_step_label,
  deadline_label,
  target_score,
  start_score,
  current_score,
  listening_score,
  reading_score,
  regularity_percent,
  regularity_label,
  risk_primary,
  risk_detail,
  weak_zones,
  coach_tip
)
values (
  '11111111-1111-1111-1111-111111111111',
  null,
  'adherent',
  'Amina S.',
  'AS',
  2,
  'Etape 2',
  'TOEIC dans 18 jours',
  785,
  520,
  615,
  325,
  290,
  86,
  '6 jours actifs sur 7',
  'Part 3',
  'Perte de precision sur questions implicites et cadence audio.',
  'Part 3, Part 7',
  'Stabilise la prise de notes en Listening avant d''augmenter le volume de tests blancs.'
)
on conflict (id) do update set
  full_name = excluded.full_name,
  avatar = excluded.avatar,
  current_step = excluded.current_step,
  current_step_label = excluded.current_step_label,
  deadline_label = excluded.deadline_label,
  target_score = excluded.target_score,
  start_score = excluded.start_score,
  current_score = excluded.current_score,
  listening_score = excluded.listening_score,
  reading_score = excluded.reading_score,
  regularity_percent = excluded.regularity_percent,
  regularity_label = excluded.regularity_label,
  risk_primary = excluded.risk_primary,
  risk_detail = excluded.risk_detail,
  weak_zones = excluded.weak_zones,
  coach_tip = excluded.coach_tip,
  updated_at = timezone('utc', now());

insert into app.program_steps (step_number, name, description, status_label, status_tone, progress_percent, progress_detail, is_active, is_locked)
values
  (1, 'Embarquement', 'Cadre d''execution, outils et tableau de bord.', 'Completee', 'badge-success', 100, 'Etape terminee.', false, false),
  (2, 'Listening', 'Travail de cadence, precision et endurance audio.', 'Active', 'badge-accent', 62, 'Bon rythme, encore instable sur les implicites.', true, false),
  (3, 'Reading', 'Lecture business, pression du temps et grammaire en contexte.', 'Verrouillee', '', null, '', false, true),
  (4, 'Deep Boost 2.0', 'Renforcement et automatisation.', 'Verrouillee', '', null, '', false, true),
  (5, 'Anti Derangement', 'Preparation mentale et execution finale.', 'Verrouillee', '', null, '', false, true)
on conflict (step_number) do update set
  name = excluded.name,
  description = excluded.description,
  status_label = excluded.status_label,
  status_tone = excluded.status_tone,
  progress_percent = excluded.progress_percent,
  progress_detail = excluded.progress_detail,
  is_active = excluded.is_active,
  is_locked = excluded.is_locked,
  updated_at = timezone('utc', now());

delete from app.program_step_items;
insert into app.program_step_items (step_id, label, color, sort_order)
select ps.id, v.label, v.color, v.sort_order
from app.program_steps ps
join (
  values
    (1, 'Conditions de performance', 'var(--accent)', 1),
    (1, 'Guide d''astuces', 'var(--gold)', 2),
    (2, 'Consignes speciales', 'var(--accent)', 1),
    (2, 'Neuro training', '#0098cc', 2),
    (2, 'Challenge mode', 'var(--gold)', 3),
    (3, 'Resume de grammaire', 'var(--gold)', 1),
    (3, 'Business reading', 'var(--accent)', 2),
    (4, 'Revision ciblee', 'var(--success)', 1),
    (5, 'Mindset', 'var(--danger)', 1)
) as v(step_number, label, color, sort_order)
  on ps.step_number = v.step_number;

delete from app.score_entries where profile_id = '11111111-1111-1111-1111-111111111111';
insert into app.score_entries (profile_id, taken_on, listening, reading, format_label, is_current)
values
  ('11111111-1111-1111-1111-111111111111', '2026-04-12', 260, 260, 'Diagnostic', false),
  ('11111111-1111-1111-1111-111111111111', '2026-04-19', 285, 270, 'Retest', false),
  ('11111111-1111-1111-1111-111111111111', '2026-04-26', 305, 280, 'Retest', false),
  ('11111111-1111-1111-1111-111111111111', '2026-05-02', 325, 290, 'Retest', true);

delete from app.score_analysis where profile_id = '11111111-1111-1111-1111-111111111111';
insert into app.score_analysis (profile_id, part_label, percent, level_label)
values
  ('11111111-1111-1111-1111-111111111111', 'Part 1', 82, 'Bon'),
  ('11111111-1111-1111-1111-111111111111', 'Part 2', 76, 'Bon'),
  ('11111111-1111-1111-1111-111111111111', 'Part 3', 49, 'Faible'),
  ('11111111-1111-1111-1111-111111111111', 'Part 4', 58, 'Moyen'),
  ('11111111-1111-1111-1111-111111111111', 'Part 5', 71, 'Bon'),
  ('11111111-1111-1111-1111-111111111111', 'Part 6', 54, 'Moyen'),
  ('11111111-1111-1111-1111-111111111111', 'Part 7', 51, 'Moyen');

delete from app.notes where profile_id = '11111111-1111-1111-1111-111111111111';
with inserted_notes as (
  insert into app.notes (id, profile_id, title, meta, step_label, content, tag)
  values
    (
      '22222222-2222-2222-2222-222222222221',
      '11111111-1111-1111-1111-111111111111',
      'Erreurs Part 3',
      'Mise a jour le 2026-05-02',
      'Listening',
      'Je perds le fil quand deux distracteurs se ressemblent. Revenir au mot-cle de la question avant les choix.',
      'Prioritaire'
    ),
    (
      '22222222-2222-2222-2222-222222222222',
      '11111111-1111-1111-1111-111111111111',
      'Routine avant session',
      'Mise a jour le 2026-05-01',
      'Embarquement',
      'Casque, timer, feuille de notes, pas de telephone.',
      null
    )
  returning id
)
select 1;

delete from app.note_words
where note_id in (
  '22222222-2222-2222-2222-222222222221',
  '22222222-2222-2222-2222-222222222222'
);

insert into app.note_words (note_id, word, state)
values
  ('22222222-2222-2222-2222-222222222221', 'shipment', 'review'),
  ('22222222-2222-2222-2222-222222222221', 'delay', 'mastered');

delete from app.resources;
insert into app.resources (id, title, meta, category, icon, tone_class, is_locked)
values
  ('33333333-3333-3333-3333-333333333331', 'Resume de grammaire', 'Support fondamental pour Reading', 'Methode', 'GR', 'badge-accent', false),
  ('33333333-3333-3333-3333-333333333332', 'Feuille de prise de notes', 'A utiliser pendant les sessions Listening', 'Methode', 'NT', 'badge-success', false),
  ('33333333-3333-3333-3333-333333333333', 'Challenge mode', 'Debloque en etape active', 'Exercices', 'CM', 'badge-accent', false),
  ('33333333-3333-3333-3333-333333333334', 'Deep Boost 2.0', 'Acces apres validation de l''etape 3', 'Exercices', 'DB', '', true);

delete from app.resource_statuses;
insert into app.resource_statuses (resource_id, label, tone, sort_order)
values
  ('33333333-3333-3333-3333-333333333331', 'Disponible', 'badge-accent', 1),
  ('33333333-3333-3333-3333-333333333331', 'Essentiel', 'badge-gold', 2),
  ('33333333-3333-3333-3333-333333333332', 'Disponible', 'badge-success', 1),
  ('33333333-3333-3333-3333-333333333333', 'Etape 2', 'badge-accent', 1),
  ('33333333-3333-3333-3333-333333333333', 'Actif', 'badge-success', 2),
  ('33333333-3333-3333-3333-333333333334', 'Verrouille', '', 1);

delete from app.support_messages where profile_id = '11111111-1111-1111-1111-111111111111';
insert into app.support_messages (profile_id, sender_name, sender_avatar, sent_at, is_read, content, border_color)
values
  (
    '11111111-1111-1111-1111-111111111111',
    'Coach support',
    'CS',
    '2026-05-02T21:00:00Z',
    false,
    'J''ai bien recu ton dernier score. Continue le protocole Listening sur 48 h avant un nouveau retest.',
    '#22d3ff'
  ),
  (
    '11111111-1111-1111-1111-111111111111',
    'Equipe Deep Training',
    'DT',
    '2026-05-01T10:15:00Z',
    true,
    'Tes acces de l''etape 2 sont actifs. Pense a utiliser la feuille de notes pendant chaque session.',
    '#f5a623'
  );

delete from app.chat_messages where profile_id = '11111111-1111-1111-1111-111111111111';
insert into app.chat_messages (profile_id, role, content, sent_at)
values
  ('11111111-1111-1111-1111-111111111111', 'assistant', 'Tu es en etape Listening. La priorite est la precision avant la vitesse brute.', '2026-05-02T20:30:00Z'),
  ('11111111-1111-1111-1111-111111111111', 'user', 'Quelle est ma priorite cette semaine ?', '2026-05-02T20:31:00Z'),
  ('11111111-1111-1111-1111-111111111111', 'assistant', 'Stabiliser Part 3, consolider la prise de notes, puis refaire un retest court.', '2026-05-02T20:31:30Z');

delete from app.activity_entries where profile_id = '11111111-1111-1111-1111-111111111111';
insert into app.activity_entries (profile_id, happened_at, action_label, type_label)
values
  ('11111111-1111-1111-1111-111111111111', '2026-05-02T20:10:00Z', 'Retest Listening', 'Score'),
  ('11111111-1111-1111-1111-111111111111', '2026-05-02T18:40:00Z', 'Ajout d''une note Part 3', 'Notes'),
  ('11111111-1111-1111-1111-111111111111', '2026-05-01T21:05:00Z', 'Message envoye au support', 'Support');

delete from app.daily_missions where profile_id = '11111111-1111-1111-1111-111111111111';
insert into app.daily_missions (profile_id, mission_number, title, subtitle, priority, sort_order)
values
  ('11111111-1111-1111-1111-111111111111', '01', 'Neuro training Listening', '25 min ciblees sur concentration et vitesse.', 'urgent', 1),
  ('11111111-1111-1111-1111-111111111111', '02', 'Relecture des notes', 'Corriger les erreurs recurrentes des deux derniers tests.', 'warn', 2),
  ('11111111-1111-1111-1111-111111111111', '03', 'Question au Coach IA', 'Valider le protocole des prochaines 48 h.', 'info', 3);

create or replace view app.v_adherent_dashboard as
select
  p.id as profile_id,
  p.full_name,
  p.avatar,
  p.current_step,
  p.current_step_label,
  p.deadline_label,
  p.start_score,
  p.current_score,
  p.target_score,
  p.listening_score,
  p.reading_score,
  p.regularity_percent,
  p.regularity_label,
  p.risk_primary,
  p.risk_detail,
  p.weak_zones,
  p.coach_tip
from app.profiles p;

-- Exposer explicitement le schema app a PostgREST/Supabase REST.
alter role authenticator set pgrst.db_schemas = 'public, graphql_public, app';

-- Donner les droits de base sur le schema custom.
grant usage on schema app to anon, authenticated, service_role;
grant all on all tables in schema app to anon, authenticated, service_role;
grant all on all routines in schema app to anon, authenticated, service_role;
grant all on all sequences in schema app to anon, authenticated, service_role;

alter default privileges for role postgres in schema app
grant all on tables to anon, authenticated, service_role;

alter default privileges for role postgres in schema app
grant all on routines to anon, authenticated, service_role;

alter default privileges for role postgres in schema app
grant all on sequences to anon, authenticated, service_role;

-- Forcer PostgREST a recharger la config et le cache de schema.
notify pgrst, 'reload config';
notify pgrst, 'reload schema';
