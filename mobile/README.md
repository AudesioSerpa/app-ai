# Facilita AI — Android (Capacitor)

Wrapper Android nativo (Capacitor 6) que abre o Facilita AI direto do backend
de produção em WebView. Todo o login, IA, favoritos, histórico, Mercado Pago
e regras de negócio ficam no servidor — **nenhuma chave/segredo vai dentro do APK**.

## Configuração

| Item              | Valor                                     |
|-------------------|-------------------------------------------|
| Nome              | Facilita AI                               |
| Package (appId)   | `com.facilitaai.app`                      |
| Versão            | `1.0.0` (versionCode `1`)                 |
| URL de produção   | `https://smart-tools-49.emergent.host`    |
| Permissões        | `INTERNET` apenas                         |
| minSdk / target   | 22 / 35 (Capacitor 6 default)             |
| Splash            | Laranja `#FF5722` com o logo do app       |

## Como o app funciona
1. `capacitor.config.json` define `server.url` apontando para produção.
2. A `MainActivity` do Capacitor abre a WebView diretamente nessa URL.
3. Login/JWT, Mercado Pago Preapproval, IA, tudo continua no backend.
4. Se a rede cair, o app mostra `www/offline.html` (empacotado no APK).

## Build do APK/AAB pelo GitHub Actions (recomendado)

1. Faça push desta pasta (`/mobile`) e do arquivo `.github/workflows/android.yml`
   para um repositório GitHub.
2. Vá em **Actions → Android build (Facilita AI) → Run workflow**
   (ou faça um push que altere `mobile/**`).
3. O workflow gera dois artifacts:
   - **`facilita-ai-debug-apk`** — APK debug pronto para instalar no celular
     (baixe, envie para o Android e permita "Instalar de fontes desconhecidas").
   - **`facilita-ai-release-aab`** — AAB pronto para subir na Google Play Console.

### Assinatura para a Google Play (obrigatória para publicar)

Gere seu keystore localmente:

```bash
keytool -genkey -v -keystore facilita-ai.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias facilita-ai
```

No GitHub, vá em **Settings → Secrets and variables → Actions → New repository secret**
e crie 4 secrets:

| Nome                        | Valor                                             |
|-----------------------------|---------------------------------------------------|
| `ANDROID_KEYSTORE_BASE64`   | `base64 -w0 facilita-ai.jks` (cole o resultado)   |
| `ANDROID_KEYSTORE_PASSWORD` | senha do keystore                                 |
| `ANDROID_KEY_ALIAS`         | `facilita-ai`                                     |
| `ANDROID_KEY_PASSWORD`      | senha da chave                                    |

Rode o workflow de novo — o AAB sai assinado e válido para a Play.

## Build local (Android Studio)

```bash
cd mobile
yarn install
npx cap sync android
npx cap open android    # abre no Android Studio
# → Build → Generate Signed Bundle / APK
```

Requer JDK 21 + Android Studio Hedgehog+ com Android SDK 35.

## Trocar de URL (ambiente)

Basta editar `capacitor.config.json > server.url` e rodar `npx cap sync android`.
Nunca aponte para o preview (`*.preview.emergentagent.com`) em builds distribuídos.
