@echo off
setlocal enabledelayedexpansion

rem dossier de base
set "install_folder=C:\Tools\ch-jdk-changer"

rem Si le script est déjà dans le dossier d'installation, démarrer directement
if /i "%~dp0"=="!install_folder!\" (
    goto :start_script
)

rem Si le dossier d'installation n'existe pas, le créer
if not exist "!install_folder!" (
    mkdir "!install_folder!"
)

rem Copier le script dans le dossier d'installation
copy /Y "%~f0" "!install_folder!\ch.bat"

rem Ajout au PATH
setx PATH "!install_folder!;%PATH%"

echo Script installé dans !install_folder!
echo !install_folder! ajouté au PATH. Utilisez 'ch' partout.
echo Vous devez ouvrir une nouvelle invite de commande pour voir les changements.

rem Supprimer le fichier batch d'origine
del "%~f0"

rem Fermer la session du terminal
exit /b

:start_script
rem Maintenant, continuer avec les fonctions du script

set "verbose=0"
if "%3"=="-o" (
    set "verbose=1"
    shift
)

set "supported_versions=8 17 21 23 25"

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

if "%1"=="global" (
    if "%2"=="" (
        echo Veuillez specifier une version.
        exit /b 1
    )
    set "version=%2"

    rem chercher java de maniere recursive
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
    echo Commandes disponibles :
    echo  list        : Liste les versions Java disponibles sur votre systeme
    echo  global [version] : Defini la version Java [version] comme version globale pour votre environnement
    echo  -v         : Affiche la version du script 'ch'
    echo  help       : Affiche L'aide
    echo.
    exit /b 0
)

echo Commande non reconnue. Utilisez 'ch help' pour obtenir de l'aide.
exit /b 1
