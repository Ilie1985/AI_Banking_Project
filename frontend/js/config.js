const LOCAL_API_BASE = "http://127.0.0.1:8000";
const LIVE_API_BASE = "https://ai-banking-backend-x040.onrender.com";

const IS_LOCAL_FRONTEND =
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname === "localhost";

const API_BASE = IS_LOCAL_FRONTEND ? LOCAL_API_BASE : LIVE_API_BASE;

const SUPABASE_URL = window.APP_CONFIG?.SUPABASE_URL || "";
const SUPABASE_ANON_KEY = window.APP_CONFIG?.SUPABASE_ANON_KEY || "";

let supabaseClient = null;
let currentUser = null;

let categoryChart = null;
let monthlyTrendChart = null;
let analysisCategoryChart = null;
let analysisMonthlyChart = null;
let forecastChart = null;

let currentTransactionLimit = 5;
let currentDataMode = "mock";
let currentBudgetItems = {};