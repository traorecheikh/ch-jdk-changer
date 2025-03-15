@echo off
setlocal enabledelayedexpansion

rem Define the folder where we will install the script
set "install_folder=C:\Tools\ch-jdk-changer"

rem Create the folder if it doesn't exist
if not exist "!install_folder!" (
    mkdir "!install_folder!"
)

rem Move the current script to the install folder
rem This assumes the script is already downloaded in the current directory
rem and will move itself to the install folder
move /Y "%~f0" "!install_folder!\first.bat"

rem Add the folder to the system PATH
setx PATH "!install_folder!;%PATH%"

rem Inform the user about the changes
echo %date% %time% - Le script a ete installe dans !install_folder!
echo %date% %time% - Le dossier !install_folder! a ete ajoute au PATH. Utilisez 'ch' partout.

rem Now proceed with the actual script functions

set "verbose=0"
if "%2"=="-o" (
    set "verbose=1"
    set "shiftcount=1"
    shift
)

if "%1"=="list" (
    echo %date% %time% - Liste des versions de Java disponibles :
    set "found=0"
    for /d %%i in (jdk-*) do (
        set "folder=%%i"
        if exist "%%i\bin\java.exe" (
            set "version=!folder:jdk-=!"
            if !verbose! equ 1 (
                echo !date! !time! - Trouvé: !version! - !folder!
            ) else (
                echo !version!
            )
            set found=1
        )
    )
    if not !found! == 1 (
        echo %date% %time% - Aucun dossier Java trouve.
        exit /b 1
    )
    exit /b 0
)

if "%1"=="global" (
    if "%2"=="" (
        echo %date% %time% - Veuillez specifier une version.
        exit /b 1
    )
    set "version=%2"
    if not exist "jdk-!version!\bin\java.exe" (
        echo %date% %time% - La version specifiee !version! n'existe pas ou le dossier est incorrect.
        exit /b 1
    )

    echo %date% %time% - Definition de JAVA_HOME sur le dossier jdk-!version!
    set "JAVA_HOME=%CD%\jdk-!version!"
    setx JAVA_HOME "!JAVA_HOME!"
    echo %date% %time% - JAVA_HOME defini sur !JAVA_HOME!

    set "current_path=!PATH!"
    set "new_path="
    echo %date% %time% - Mise a jour du repertoire...
    for %%a in ("!current_path:;=";"!") do (
        set "part=%%~a"
        set "match=0"
        echo !part! | find /i "!CD!\jdk-" >nul
        if !errorlevel! equ 0 (
            echo !part! | find /i "\bin" >nul
            if !errorlevel! equ 0 set "match=1"
        )
        if !match! equ 0 (
            if "!new_path!"=="" (
                set "new_path=!part!"
            ) else (
                set "new_path=!new_path!;!part!"
            )
        )
    )
    set "new_path=!JAVA_HOME!\bin;!new_path!"
    setx PATH "!new_path!"
    echo %date% %time% - PATH mis a jour. Ouvrez une nouvelle invite de commande pour voir les changements.

    exit /b 0
)

if "%1"=="help" (
    echo %date% %time% - Aide pour ch java :
    echo.
    echo ch list        : Affiche les versions disponibles
    echo ch global [version] : Definit la version a utiliser
    echo ch help        : Affiche cette aide
    exit /b 0
)

echo %date% %time% - Commande non reconnue. Utilisez 'ch help' pour l'aide.
exit /b 1
