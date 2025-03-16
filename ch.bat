@echo off
setlocal enabledelayedexpansion

rem Installer block – copy script into fixed folder and add to PATH if not already installed
set "install_folder=C:\Tools\ch-jdk-changer"
if /i "%~dp0"=="!install_folder!\" (
    goto :start_script
)
if not exist "!install_folder!" (
    mkdir "!install_folder!"
)
copy /Y "%~f0" "!install_folder!\ch.bat"
setx PATH "!install_folder!;%PATH%"
echo Script installe dans !install_folder!
echo !install_folder! ajoute au PATH. Utilisez 'ch' partout.
exit /b

:start_script

set "verbose=0"
if "%3"=="-o" (
    set "verbose=1"
    shift
)

set "supported_versions=8 17 21 23 25"

rem Display script version
if "%1"=="-v" (
    echo(
    echo      ___           ___                  ___         _____          ___     
    echo     /  /\         /__/\                /  /\       /  /::\        /__/^|    
    echo    /  /:/         \  \:\              /  /:/      /  /:/\:\      ^|  ^|:^|    
    echo   /  /:/           \__\:\            /__/::\     /  /:/  \:\     ^|  ^|:^|    
    echo  /  /:/  ___   ___ /  /::\           \__\/\:\   /__/:/ \__\^:^|  __^|  ^|:^|    
    echo /__/:/  /  /\ /__/\  /:/\:\             \  \:\  \  \:\ /  /:/ /__/\_^|:^|____
    echo \  \:\ /  /:/ \  \:\/:/__\/              \__\:\  \  \:\  /:/  \  \:\/:::::/
    echo  \  \:\  /:/   \  \::/                   /  /:/   \  \:\/:/    \  \::/~~~~ 
    echo   \  \:\/:/     \  \:\                  /__/:/     \  \::/      \  \:\     
    echo    \  \::/       \  \:\                 \__\/       \__\/        \  \:\    
    echo     \__\/         \__\/                                           \__\/    
    echo par Cheikh Tidiane
    echo Version: 1.13.27
    echo(
    exit /b
)

if "%1"=="list" (
    echo Versions Java disponibles :
    set "found=0"
    for %%v in (%supported_versions%) do (
        for /d %%i in (
            "C:\Program Files\Java\*jdk-%%v*"
            "C:\Program Files (x86)\Java\*jdk-%%v*"
            "C:\Program Files\Java\*openjdk-%%v*"
            "C:\Program Files (x86)\Java\*openjdk-%%v*"
        ) do (
            if exist "%%i\bin\java.exe" (
                if !verbose! equ 1 (
                    echo Trouve: %%v - %%i
                ) else (
                    echo %%v
                )
                set "found=1"
            )
        )
    )
    if not !found! == 1 (
        echo Aucun Java trouve.
        exit /b 1
    )
    exit /b 0
)

if "%1"=="global" (
    if "%2"=="" (
        echo Veuillez specifier une version.
        exit /b 1
    )
    set "version=%2"
    set "folder="
    set "found=0"
    
    for /f "delims=" %%i in ('dir /b /ad "C:\Program Files\Java\jdk-!version!*" 2^>nul') do (
         set "folder=C:\Program Files\Java\%%i"
         set "found=1"
         goto :found
    )
    if "!found!"=="0" (
       for /f "delims=" %%i in ('dir /b /ad "C:\Program Files (x86)\Java\jdk-!version!*" 2^>nul') do (
           set "folder=C:\Program Files (x86)\Java\%%i"
           set "found=1"
           goto :found
       )
    )
    if "!found!"=="0" (
       for /f "delims=" %%i in ('dir /b /ad "C:\Program Files\Java\openjdk-!version!*" 2^>nul') do (
           set "folder=C:\Program Files\Java\%%i"
           set "found=1"
           goto :found
       )
    )
    if "!found!"=="0" (
       for /f "delims=" %%i in ('dir /b /ad "C:\Program Files (x86)\Java\openjdk-!version!*" 2^>nul') do (
           set "folder=C:\Program Files (x86)\Java\%%i"
           set "found=1"
           goto :found
       )
    )
    if "!found!"=="0" (
         echo La version specifiee !version! n'existe pas ou le dossier est incorrect.
         exit /b 1
    )
    :found
    if not exist "!folder!\bin\java.exe" (
         echo Le dossier trouve ne contient pas java.exe.
         exit /b 1
    )
    
    echo Definition de JAVA_HOME sur le dossier !folder!
    setx JAVA_HOME "!folder!"
    
    rem Use the resolved folder's bin path
    set "literal_path=!folder!\bin"
    
    rem Retrieve the current PATH from registry
    set "original_path="
    for /f "tokens=3*" %%A in ('reg query HKCU\Environment /v Path 2^>nul ^| findstr /i "Path"') do (
        set "original_path=%%A %%B"
    )
    
    rem Rebuild PATH filtering out any token that contains \Java\jdk- or \Java\openjdk-
    set "filtered_path="
    for %%P in ("!original_path:;=";"!") do (
        set "token=%%~P"
        echo !token! | findstr /i "\\Java\\jdk-" >nul
        if errorlevel 1 (
            echo !token! | findstr /i "\\Java\\openjdk-" >nul
            if errorlevel 1 (
                if defined filtered_path (
                    set "filtered_path=!filtered_path!;!token!"
                ) else (
                    set "filtered_path=!token!"
                )
            )
        )
    )
    
    rem Prepend the new literal_path to the filtered PATH
    echo Verification de la presence de !literal_path! dans le PATH.
    rem (No need to check if already present because we removed any prior Java paths)
    set "new_path=!literal_path!;!filtered_path!"
    echo Ajout de !literal_path! au PATH.
    setx PATH "!new_path!"
    echo PATH mis a jour avec !literal_path!.
    
    echo JAVA_HOME mis a jour pour la version !version!. Ouvrez une nouvelle invite de commande pour voir les changements.
    exit /b 0
)

rem Help command
if "%1"=="help" (
    echo.
    echo Commandes disponibles :
    echo  list             : Liste les versions Java disponibles sur votre systeme
    echo  global [version] : Defini la version Java [version] comme version globale pour votre environnement
    echo  -v               : Affiche la version du script 'ch'
    echo  help             : Affiche L'aide
    echo.
    exit /b 0
)

echo Commande non reconnue. Utilisez 'ch help' pour obtenir de l'aide.
exit /b 1
