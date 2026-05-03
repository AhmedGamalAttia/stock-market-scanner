import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export const supabase =
  url && anon
    ? createClient(url, anon, {
        auth: { persistSession: false },
        global: { fetch: (...args) => fetch(...args) },
      })
    : null;

export const supabaseConfigured = Boolean(url && anon);
