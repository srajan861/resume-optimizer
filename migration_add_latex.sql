-- Add latex_code column to resumes table
ALTER TABLE public.resumes ADD COLUMN IF NOT EXISTS latex_code TEXT;
