@echo off
setlocal enabledelayedexpansion

rem Define the folder where we will install the script
set "install_folder=C:\Tools\ch-jdk-changer"

rem Check if the script is already installed in the correct folder
if /i "%~dp0"=="!install_folder!\" (
    rem If it's already in the target folder, skip the install process
    goto :start_script
)

rem Create the folder if it doesn't exist
if not exist "!install_folder!" (
    mkdir "!install_folder!"
)

rem Copy the script to the install folder (no move, just copy)
copy /Y "%~f0" "!install_folder!\ch.bat"

rem Add the folder to the system PATH
setx PATH "!install_folder!;%PATH%"

rem Inform the user about the changes
echo Script installe dans !install_folder!
echo !install_folder! ajoute au PATH. Utilisez 'ch' partout.

rem Exit the current session to prevent further actions
exit /b

:start_script
rem Now proceed with the actual script functions

set "verbose=0"
if "%3"=="-o" (
    set "verbose=1"
    shift
)

rem Define supported versions (8, 17, 21, 23, 25)
set "supported_versions=8 17 21 23 25"

rem Display script version
if "%1"=="-v" (
    echo.
    echo  .,-:::::   ::   .: .,::::::  ::: :::  .    ::   .:    :::::::::::::::::::..    :::.         ...    :::::::..  .,::::::  
    echo ,;;;'````'  ,;;   ;;,;;;;''''  ;;; ;;; .;;,.,;;   ;;,   ;;;;;;;;'''';;;;``;;;;   ;;`;;     .;;;;;;;. ;;;;``;;;; ;;;;''''  
    echo sss        ,sss,,,ooo oooo   ooo   ooo/' ,ddd,,,ddd          hh       oo,/hh'  ,oo 'hh,  ,hh     \hh,hhh,/ddd'  ddcccc   
    echo $$$        "$$$"""$$$ $$""""   $$$_$$$$,   "$$$"""$$$        $$      $$$$$$c   c$$$cc$$$c $$$,     $$$$$$$$$c    $$""""   
    echo `88bo,__,o, 888   "88o888oo,__ 888"888"88o, 888   "88o       88,     888b "88bo,888   888,"888,_ _,88P888b "88bo,888oo,__ 
    echo   "YUMMMMMP"MMM    YMM""""YUMMMMMM MMM "MMP"MMM    YMM       MMM     MMMM   "W" YMM   ""`   "YMMMMMP" MMMM   "W" """"YUMMM
    echo.
    echo Version: 1.0.0
    echo.
    exit /b
)


rem List available Java versions
if "%1"=="list" (
    echo Versions Java disponibles :
    set "found=0"
    
    for %%v in (%supported_versions%) do (
        for /d %%i in ("C:\Program Files\Java\*jdk-%%v*" "C:\Program Files (x86)\Java\*jdk-%%v*" "C:\Program Files\Java\*openjdk-%%v*" "C:\Program Files (x86)\Java\*openjdk-%%v*") do (
            set "folder=%%i"
            if exist "%%i\bin\java.exe" (
                set "version=%%v"
                if !verbose! equ 1 (
                    echo Trouve: !version! - !folder!
                ) else (
                    echo !version!
                )
                set found=1
            )
        )
    )
    
    if not !found! == 1 (
        echo Aucun Java trouve.
        exit /b 1
    )
    exit /b 0
)

rem Check if the script is invoked with the "global" command
if "%1"=="global" (
    if "%2"=="" (
        echo Veuillez specifier une version.
        exit /b 1
    )
    set "version=%2"

    rem Search for the JDK folder (works for Program Files, Program Files (x86), etc.)
    set "found=0"
    for /d %%i in ("C:\Program Files\Java\*jdk-%version%*" "C:\Program Files (x86)\Java\*jdk-%version%*") do (
        if exist "%%i\bin\java.exe" (
            set "folder=%%i"
            set "found=1"
        )
    )

    if !found! == 0 (
        echo La version specifiee !version! n'existe pas ou le dossier est incorrect.
        exit /b 1
    )

    rem Set JAVA_HOME
    echo Definition de JAVA_HOME sur le dossier !folder!
    set "JAVA_HOME=!folder!"
    setx JAVA_HOME "!JAVA_HOME!"

    rem Update the PATH variable
    set "current_path=!PATH!"
    set "new_path="
    for %%a in ("!current_path:;=";"!") do (
        set "part=%%~a"
        set "match=0"
        echo !part! | find /i "!folder!\bin" >nul
        if !errorlevel! equ 0 set "match=1"
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

    echo PATH mis a jour. Ouvrez une nouvelle invite de commande pour voir les changements.
    exit /b 0
)





rem Help command
if "%1"=="help" (
    echo.
    echo *** Aide pour le script 'ch' ***
    echo.
    echo Ce script permet de configurer et de changer facilement la version de Java utilisee sur votre systeme.
    echo Il vous permet de :
    echo 1. Lister les versions de Java installees sur votre machine.
    echo 2. Definir une version Java comme version globale pour l'environnement.
    echo 3. Afficher la version du script lui-meme.
    echo.
    echo Commandes disponibles :
    echo  ch list        : Liste les versions Java disponibles sur votre systeme
    echo  ch global [version] : Defini la version Java [version] comme version globale pour votre environnement
    echo  ch -v         : Affiche la version du script 'ch'
    echo  ch help       : Affiche cette aide
    echo.
    exit /b 0
)

echo Commande non reconnue. Utilisez 'ch help' pour obtenir de l'aide.
exit /b 1
