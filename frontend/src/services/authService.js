
import api from "./api";

const TOKEN_KEY = "campuscare_access_token";

export async function login(email, password) {
  const formData = new URLSearchParams();

  formData.append("username", email.trim().toLowerCase());
  formData.append("password", password);

  const response = await api.post("/api/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  sessionStorage.setItem(TOKEN_KEY, response.data.access_token);

  return response.data;
}

export async function registerStudent(studentData) {
  const response = await api.post("/api/auth/register", {
    full_name: studentData.full_name,
    email: studentData.email.trim().toLowerCase(),
    password: studentData.password,
  });

  return response.data;
}

export async function getCurrentStudent() {
  const response = await api.get("/api/auth/me");
  return response.data;
}

export function logout() {
  sessionStorage.removeItem(TOKEN_KEY);
}

export function getAccessToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function getSessionRole() {
  const token = getAccessToken();

  if (!token) return null;

  try {
    const payload = token.split(".")[1];
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");

    const decoded = decodeURIComponent(
      Array.from(atob(base64), (character) =>
        `%${character.charCodeAt(0).toString(16).padStart(2, "0")}`
      ).join("")
    );

    return JSON.parse(decoded).role ?? null;
  } catch {
    return null;
  }
}
