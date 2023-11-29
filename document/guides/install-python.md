# Python install guide

<details>
<summary>Windows</summary>

## Install pyenv-win

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```

If you get a permissions error, open PowerShell as an administrator,
run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`, then reopen PowerShell and run the command again.

## Install Python

```powershell
pyenv install 3.9.13
pyenv global 3.9.13
```

If you are told that the command pyenv cannot be found, try the following steps.

1. Restart Power Shell or Terminal to reflect the path change
2. Win+R -> "SystemPropertiesAdvanced" and Enter -> "Environment Variables" -> "Path" of user or system environment
   variables -> "
   Edit" -> "New" -> Add "C:\Users\{Username}\.pyenv\pyenv-win\bin" and “C:\Users\{username}\.pyenv\pyenv-win\shims”

</details>

<details>
<summary>macOS</summary>

## Install pyenv

```bash
brew install pyenv
```

## Install Python

```bash
pyenv install 3.9.18
pyenv global 3.9.18
```

If you get an error with `pyenv install`, run `xcode-select --install`, restart your terminal, and try again. If the
shell you are running is bash, add the following line to `~/.bash profile`, and if you are using zsh, add the following
line to `~/.zshrc`.

```bash
eval "$(pyenv init --path)"
```

If the shell you are running is fish, add the following line to `~/.config/fish/config.fish`.

```bash
status --is-interactive; and pyenv init - | source
```

</details>

<details>
<summary>Linux</summary>

## Install pyenv

```bash
curl https://pyenv.run | bash
```

## Install Python

```bash
pyenv install 3.9.18
pyenv global 3.9.18
```

If you get an error with `pyenv install`, see below instructions and try again.

<details>
<summary>Ubuntu</summary>

```bash
sudo apt update
sudo apt install build-essential libffi-dev libssl-dev zlib1g-dev liblzma-dev libbz2-dev libreadline-dev libsqlite3-dev libopencv-dev tk-dev git
```

</details>

<details>
<summary>CentOS</summary>

```bash
sudo yum update
sudo yum install gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel git
```

</details>

<details>
<summary>Arch Linux</summary>

```bash
sudo pacman -Syu
sudo pacman -S base-devel openssl zlib xz tk git
```

</details>

</details>