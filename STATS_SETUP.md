# Activar estadísticas privadas

1. En tu sesión de **Vicenkks**, abre https://github.com/settings/personal-access-tokens/new.
2. Crea un token fine-grained con una caducidad adecuada, Resource owner `Vicenkks` y los repositorios que quieras incluir. Usa **All repositories** si quieres incluir todos tus repositorios propios presentes y futuros. En Repository permissions concede **Contents: Read-only**; Metadata se incluye automáticamente. No necesita escritura.
3. En https://github.com/Vicenkks/Vicenkks/settings/secrets/actions crea un repository secret llamado `PROFILE_STATS_TOKEN` y pega allí el token. No lo guardes en archivos ni lo pegues en un chat. Si otras personas tienen escritura en este repositorio, pueden modificar el workflow para acceder al secreto: en ese caso ejecuta la automatización desde un repositorio privado sin esos colaboradores.
4. Sube estos archivos desde el clon:

   ```bash
   git add README.md scripts/profile_stats.py .github/workflows/profile-stats.yml assets/github-stats.svg STATS_SETUP.md
   git commit -m "Generate profile analytics including private repositories"
   git push origin main
   ```

5. En GitHub abre **Actions → Update profile statistics → Run workflow → Run workflow**. El workflow también se ejecuta diariamente a las 06:17 UTC.
6. Cuando termine, la imagen del README mostrará los datos reales. Usa `git pull --ff-only` para descargar la imagen actualizada al clon.

## Qué se cuenta

- Repositorios propios accesibles al token, separados en públicos y privados. No incluye repositorios de organizaciones ni aquellos donde solo colaboras.
- Lenguajes según bytes de código de la rama predeterminada, excluyendo forks. Son los 10 principales; los porcentajes usan el total de todos los lenguajes. No mide tiempo de trabajo ni dominio de una tecnología.
- Commits reconocidos como contribuciones por GitHub, consultados año por año desde la creación de la cuenta. Pueden incluir contribuciones en otros repositorios accesibles, pero no todos los commits de todas las ramas. La identidad del autor, el acceso del token y las reglas de contribución de GitHub afectan al resultado.
- Solo se publica el SVG con cifras agregadas: nunca nombres de repositorios privados ni su código.

Si el token caduca o faltan permisos, la ejecución falla y conserva la última imagen. La fecha de actualización permite detectar datos antiguos. Si hay un error 403 al hacer push, revisa **Settings → Actions → General → Workflow permissions** y las reglas de protección de `main`.
