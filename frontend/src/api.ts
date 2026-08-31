// Central API configuration pointing directly to live Render backend
export const API_BASE: string = (((import.meta as any).env?.VITE_API_URL as string) || 'https://ocean-intelligence-backend-jq3e.onrender.com').replace(/\/$/, '')
