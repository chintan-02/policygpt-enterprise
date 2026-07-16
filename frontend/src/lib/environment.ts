import "server-only";

const DEVELOPMENT_BACKEND_URL = "http://localhost:8000";

export type PublicAppEnvironment = {
  appName: string;
  appVersion: string;
  appEnvironment: string;
};

export class ServerEnvironmentError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ServerEnvironmentError";
  }
}

export function getPublicAppEnvironment(): PublicAppEnvironment {
  return {
    appName: process.env.NEXT_PUBLIC_APP_NAME ?? "PolicyGPT Enterprise",
    appVersion: process.env.NEXT_PUBLIC_APP_VERSION ?? "0.3.0",
    appEnvironment: process.env.NEXT_PUBLIC_APP_ENV ?? "Local",
  };
}

export function getFastApiUrl(): string {
  const configuredUrl = process.env.FASTAPI_URL?.trim();

  if (configuredUrl) {
    return configuredUrl.replace(/\/$/, "");
  }

  if (process.env.NODE_ENV === "production") {
    throw new ServerEnvironmentError(
      "FASTAPI_URL is required for the PolicyGPT frontend in production.",
    );
  }

  return DEVELOPMENT_BACKEND_URL;
}
