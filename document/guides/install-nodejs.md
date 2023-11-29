# Node.js install guide

See [volta official page](https://volta.sh/) for more information.

<details>
<summary>Windows</summary>

## Install volta

### With winget

```powershell
winget instal Volta.Volta 
```

### Without winget

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/volta-cli/volta/releases/download/v1.1.1/volta-1.1.1-windows-x86_64.msi" -OutFile "./volta-1.1.1-windows-x86_64.msi"; &"./volta-1.1.1-windows-x86_64.msi"
```

## Install Node.js

```powershell
volta install node@lts npm
```

</details>

<details>
<summary>MacOS / Linux</summary>

## Install volta

```bash
curl https://get.volta.sh | bash
```

## Install Node.js

```bash
volta install node@lts npm
```
</details>