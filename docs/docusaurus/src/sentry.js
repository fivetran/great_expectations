import * as Sentry from "@sentry/react";
import siteConfig from "@generated/docusaurus.config";

const dsn = siteConfig.customFields?.sentryDsn;
if (dsn) {
  Sentry.init({
    dsn,
    environment: process.env.NODE_ENV,
    tracesSampleRate: 0,
  });
} else {
  console.warn("Sentry DSN not found");
}
