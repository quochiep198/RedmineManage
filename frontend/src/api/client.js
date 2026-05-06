import axios from "axios";

export const LONG_RUNNING_REQUEST_TIMEOUT_MS = 600000;

export const api = axios.create({
  baseURL: "http://localhost:8000/api",
  timeout: 10000,
  withCredentials: true,
});
