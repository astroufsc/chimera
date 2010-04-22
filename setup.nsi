
!define CHIMERA "Chimera"
!define CHIMERA_VERSION "0.2" 
!define CHIMERA_BRANDINGTEXT "Chimera - Observatory Automation System"

!include "MUI2.nsh"
!include "EnvVarUpdate.nsh"

;--------------------------------
;General

Name ${CHIMERA}
InstallDir "$PROGRAMFILES\${CHIMERA}"

CRCCheck On
RequestExecutionLevel user

OutFile "Chimera.exe"

ShowInstDetails "hide"
ShowUninstDetails "hide"

SetCompressor "LZMA"

;--------------------------------
;Interface Settings

!define MUI_ABORTWARNING

;--------------------------------
;Pages

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "COPYING"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

;--------------------------------
;Languages
 
!insertmacro MUI_LANGUAGE "English"


;-------------------------------- 
;Installer Sections     
Section "install"

    ;Add files
    SetOutPath "$INSTDIR"
    File /r dist\*.*  
    
    ${EnvVarUpdate} $0 "PATH" "A" "HKCU" $INSTDIR

    ;create start-menu items
    CreateDirectory "$SMPROGRAMS\${CHIMERA}"
    CreateShortCut "$SMPROGRAMS\${CHIMERA}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0

    ;write uninstall information to the registry
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${CHIMERA}" "DisplayName" "${CHIMERA}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${CHIMERA}" "UninstallString" "$INSTDIR\Uninstall.exe"

    WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd


;--------------------------------    
;Uninstaller Section  
Section "Uninstall"

    ;Delete Files 
    RMDir /r "$INSTDIR\*.*"    
    
    ${un.EnvVarUpdate} $0 "PATH" "R" "HKCU" $INSTDIR
    
    ;Remove the installation directory
    RMDir "$INSTDIR"

    ;Delete Start Menu Shortcuts
    Delete "$SMPROGRAMS\${CHIMERA}\Uninstall.lnk"
    RMDir  "$SMPROGRAMS\${CHIMERA}"

    ;Delete Uninstaller And Unistall Registry Entries
    DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\${CHIMERA}"
    DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${CHIMERA}"  

SectionEnd

