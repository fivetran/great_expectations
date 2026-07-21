Spark 4 requires JDK 17 or newer.

1. Run `java -version` to check your installed JDK — it should report 17 or newer. If you don't have a JDK 17+, download one from Adoptium (Eclipse Temurin): [https://adoptium.net/](https://adoptium.net/)
2. Alternatively, if you don't want to install a JDK on your host, run `docker compose up -d` in this directory to start the spark container — it bundles its own JDK.

You should now be able to run the tests via `pytest --spark`
