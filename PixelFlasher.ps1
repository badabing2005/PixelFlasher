<#PSScriptInfo
    .VERSION 1.1
    .GUID 50786e59-138e-4962-a1b0-4246504b5bf0
    .AUTHOR badabing2005@hotmail.com
    .COMPANYNAME
    .COPYRIGHT
    .TAGS
    .LICENSEURI https://github.com/badabing2005/PixelFlasher/blob/main/LICENSE
    .PROJECTURI https://github.com/badabing2005/PixelFlasher
    .ICONURI
    .EXTERNALMODULEDEPENDENCIES
    .REQUIREDSCRIPTS
    .EXTERNALSCRIPTDEPENDENCIES
    .RELEASENOTES
    .PRIVATEDATA
#>

<#
    .SYNOPSIS
        This is a Powershell script is to update a rooted Pixel phone with new factory image and retain root.

    .DESCRIPTION
        This is a Powershell script to update a rooted Pixel phone with new factory image and retain root.
        The script automates the following steps:
          - Checks for the factory image
          - Unpacks factory image
          - Checks for dependencies (adb, fastboot, 7zip, ...)
          - Unzips the factory image
          - Extracts unpatched boot.img
          - Deletes flash-all.sh and flash-base.sh (just for extra precaution)
          - Patches flash-all.bat and removes the wipe option
          - Checks and validates phone connection
          - Checks and validates that the phone model matches the factory image
          - Transfers stock boot.img to the phone
          - Detects if Magisk is installed and not hidden
          - Launches Magisk if it is not hidden
          - Waits for the user to complete the patch on the phone
              TODO: automate the previous step to magisk patch programmatically
          - Transfers patched boot.img to the PC
          - Replaces stock boot.img with patched boot.img
          - Repackages the image zip with patched boot.img
          - Reboots to bootloader and pauses
          - Launches flash_all.bat to update the phone

    .PARAMETER factoryFile
        Alias: f
        Factory image zip file, example: oriole-sq1d.220205.003-factory-a5a63f2a.zip,
        not required if it is in current directory

    .PARAMETER  help
        Alias: h
        Show Usage Help

    .PARAMETER phoneModel
        Alias: p
        Factory image zip file, example: oriole-sq1d.220205.003-factory-a5a63f2a.zip,
        default: oriole

    .PARAMETER magisk
        Alias: m
        When Magisk is hidden, you can specify the package name so that the script can launch it,
        default: com.topjohnwu.magisk

    .PARAMETER sdk
        Alias: s
        Specify path to Android SDK Platform-Tools
        not required if it is in the path or current directory

    .PARAMETER transferPath
        Alias: t
        Where stock boot.img file will be copied to (on the phone),
        default: /storage/emulated/0/Download

    .PARAMETER lessPrompts
        Alias: y
        Less Prompting, automatic answer with the correct choices to proceed.

    .PARAMETER zip
        Alias: z
        Specify path to 7zip.exe
        default: C:\Program Files\7-Zip\7z.exe
        not required if it is in the path or current directory

    .EXAMPLE
        ./PixelFlasher.ps1
           Expects the factory image to be in the current directory
           Expects adb to be in the path or current directory
           Expects fastboot to be in the path or current directory
           Expects 7z.exe to be in the path or current directory or installed in default location: C:\Program Files\7-Zip\7z.exe

    .EXAMPLE
        ./PixelFlasher.ps1 -y
           Less prompts, auto answer to run faster.
           Expects the factory image to be in the current directory
           Expects adb to be in the path or current directory
           Expects fastboot to be in the path or current directory
           Expects 7z.exe to be in the path or current directory or installed in default location: C:\Program Files\7-Zip\7z.exe

    .EXAMPLE
        ./PixelFlasher.ps1 -f c:\pixel\oriole-sq1d.220205.003-factory-a5a63f2a.zip
           Expects the factory image to be in the specified path
           Expects adb to be in the path or current directory
           Expects fastboot to be in the path or current directory
           Expects 7z.exe to be in the path or current directory or installed in default location: C:\Program Files\7-Zip\7z.exe

    .EXAMPLE
        ./PixelFlasher.ps1 -p redfin
           Used for flashing a redfin phone (Pixel 5)
           Expects the factory image to be in the current directory
           Expects adb to be in the path or current directory
           Expects fastboot to be in the path or current directory
           Expects 7z.exe to be in the path or current directory or installed in default location: C:\Program Files\7-Zip\7z.exe

    .EXAMPLE
        c:\PixelFlasher\PixelFlasher.ps1 -s C:\Android\platform-tools -z c:\Apps\7-zip\7z.exe -f c:\temp\oriole-sq1d.220205.003-factory-a5a63f2a.zip
           Default hardware Pixel 6 (oriole)
           Factory image at c:\temp\oriole-sq1d.220205.003-factory-a5a63f2a.zip
           Expects adb to be at C:\Android\platform-tools\adb.exe
           Expects fastboot to be C:\Android\platform-tools\fastboot.exe
           Expects 7z.exe to be at c:\Apps\7-zip\7z.exe

    .NOTES
        This script is based on excellent steps provided by Homeboy76 found here
        https://forum.xda-developers.com/t/guide-root-pixel-6-android-12-with-magisk.4388733/
        Please scrutinze the script before using.

    .LINK
        https://github.com/badabing2005/PixelFlasher
#>

[CmdletBinding()]
Param(
    [Parameter(Mandatory = $false, Position = 0)][Alias("f")][string]$factoryFile = "",
    [Alias("p")][string]$phoneModel = "oriole",
    [Alias("t")][string]$transferPath = "/storage/emulated/0/Download",
    [Alias("z")][string]$zip = "C:\Program Files\7-Zip\7z.exe",
    [Alias("m")][string]$magisk = "com.topjohnwu.magisk",
    [Alias("s")][string]$sdk = "",
    [Alias("y")][switch]$lessPrompts,
    [Alias("h")][switch]$help
)


#-----------------------------------------------------------------------------
#                                ShowDisclaimer Function
#-----------------------------------------------------------------------------
function ShowDisclaimer
{
    Write-Host "*******************************************************************************"
    Write-Host "PLEASE DO YOUR PART AND READ / SEARCH / RESEARCH BEFORE USING THIS SCRIPT      "
    Write-Host "AND/OR ATTEMPTING ANY MODIFICATIONS TO YOUR DEVICE.                            "
    Write-Host "THIS TOOL ASSUMES THAT YOU ALREADY KNOW HOW TO AND HAVE ALREADY UNLOCKED       "
    Write-Host "YOUR BOOTLOADER, ALREADY ROOTED YOUR DEVICE, HOW TO USE ANDROID SDK            "
    Write-Host "PLATFORM-TOOLS, 7-ZIP, ETC.                                                    "
    Write-Host "THIS TOOL IS SIMPLY MY QUICK WAY OF UPDATING THE FIRMWARE WHILE ROOTED WITH    "
    Write-Host "MAGISK, WITHOUT LOSING DATA / REQUIRING A WIPE.                                "
    Write-Host "                                                                               "
    Write-Host "MODIFYING YOUR DEVICE COMES WITH INHERENT RISKS, AND IT'S NOT MY RESPONSIBILITY"
    Write-Host "IF YOU LOSE YOUR DATA. THE SCRIPT I SHARE HAVE WORKED FOR ME, BUT THAT DOESN'T "
    Write-Host "MEAN THAT YOU MAY NOT RUN INTO PROBLEMS.  **BACKUP YOUR DATA.**                "
    Write-Host "*******************************************************************************"
}


#-----------------------------------------------------------------------------
#                                DeleteFile Function
#-----------------------------------------------------------------------------
function DeleteFile
{
    param(
        [String] $removeFile
    )
    Write-Host "  Deleting $removeFile ..." -f DarkGray
    if ((Test-Path -Path $removeFile))
    {
        Remove-Item -path $removeFile -Force
    }
}


#-----------------------------------------------------------------------------
#                          ValidateDependencies Function
#-----------------------------------------------------------------------------
function ValidateDependencies()
{
    # adb and fastboot
    if ([string]::IsNullOrEmpty($sdk))
    {
        if (-Not (TestCommandExists "adb"))
        {
            Write-Host
            Write-Host "Error: adb is not installed or not in path." -f 'red'
            Write-Host "       SDK Platform-Tools: is required ..."
            Write-Host "       You can find more info at: " -NoNewline
            Write-Host "https://developer.android.com/studio/releases/platform-tools.html" -f 'blue'
            Write-Host
            Exit 1
        }
        if (-Not (TestCommandExists "fastboot"))
        {
            Write-Host
            Write-Host "Error: fastboot is not installed or not in path." -f 'red'
            Write-Host "       SDK Platform-Tools: is required ..."
            Write-Host "       You can find more info at: " -NoNewline
            Write-Host "https://developer.android.com/studio/releases/platform-tools.html" -f 'blue'
            Write-Host
            Exit 1
        }
    }
    else
    {
        if (-Not ((Test-Path "$sdk/adb.exe") -and (Test-Path "$sdk/fastboot.exe")))
        {
            Write-Host
            Write-Host "Error: adb/fastboot is not found in the specified path: [$sdk]" -f 'red'
            Write-Host "       SDK Platform-Tools: is required ..."
            Write-Host "       You can find more info at: " -NoNewline
            Write-Host "https://developer.android.com/studio/releases/platform-tools.html" -f 'blue'
            Write-Host
            Exit 1
        }
    }
    # 7zip
    if ([string]::IsNullOrEmpty($zip))
    {
        if (-Not (TestCommandExists "7z"))
        {
            Write-Host
            Write-Host "Error: 7zip is not installed or not in path." -f 'red'
            Write-Host "       7zip is required ..."
            Write-Host "       if 7zip is installed, specify the path with -zip parameter"
            Write-Host "       To download 7zip visit: " -NoNewline
            Write-Host "https://www.7-zip.org/download.html" -f 'blue'
            Write-Host
            Exit 1
        }
    }
    else
    {
        if (-Not (Test-Path "$zip"))
        {
            Write-Host
            Write-Host "Error: 7zip is not Found in the specified path: [$zip]" -f 'red'
            Write-Host "       7z.exe: is required ..."
            Write-Host "       To download 7zip visit: " -NoNewline
            Write-Host "https://www.7-zip.org/download.html" -f 'blue'
            Write-Host
            Exit 1
        }
    }
}


#-----------------------------------------------------------------------------
#                           TestCommandExists Function
#-----------------------------------------------------------------------------
Function TestCommandExists
{
    Param(
        [Parameter(Mandatory = $true)][System.String]$theCommand,
        [ValidateSet('Alias', 'Function', 'Filter', 'Cmdlet', 'ExternalScript', 'Application', 'Script', 'Workflow', 'Configuration', 'All')][System.String]$type = ""
    )

    $result = $false
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'

    try
    {
        if ($type)
        {
            Get-Command -CommandType $type $theCommand
        }
        else
        {
            Get-Command $theCommand
        }
        Write-Host "$theCommand exists."
        $result = $true
    }
    Catch
    {
         Write-Host "$theCommand not found" -f yellow
    }
    Finally
    {
         $ErrorActionPreference = $oldPreference
    }
    return $result
}


#-----------------------------------------------------------------------------
#                             CheckPhoneConnection Function
#-----------------------------------------------------------------------------
Function CheckPhoneConnection($deviceMode = "adb")
{
    Write-Host
    Write-Host "Please make sure your phone is plugged in and accessible via adb"
    Write-Host "---------------------------"
    Write-Host "C  = Check phone connection"
    Write-Host "A  = Abort"
    Write-Host "---------------------------"
    Write-Host "Please make a selection > " -NoNewline

    if ($lessPrompts)
    {
        $prompt = "c"
        Write-Host "  [lessPrompt] option is selected: Bypassing Prompt ..." -f DarkGray
    }
    else
    {
        $key = $Host.UI.RawUI.ReadKey()
        Write-Host
        $prompt = [string]$key.Character
    }

    if ($prompt.toLower() -eq "a")
    {
        Write-Host "Aborted!" -f red
        exit
    }
    elseif ([string]::IsNullOrEmpty($prompt))
    {
        Write-Host
        Write-Host "Please make a valid selection"
        CheckPhoneConnection -deviceMode $deviceMode
    }
    elseif ($prompt.toLower() -eq "c")
    {
        if ($deviceMode -eq "fastboot")
        {
            # check if device is in fastboot mode
            Write-Host "Checking if the phone is in bootloader mode ..." -f yellow
            $fastbootCheck = (& $fastboot devices)
            if ([string]::IsNullOrEmpty($fastbootCheck))
            {
                Write-Host "Phone is not connected or not in bootloader mode" -f red
                Write-Host "$fastbootCheck"
                CheckPhoneConnection -deviceMode $deviceMode
            }
            else
            {
                Write-Host "Phone connection is good" -f DarkGreen
            }
        }
        else
        {
            # Check if a Pixel is connected and get some basic info
            Write-Host "Checking if the phone is connected and getting basic information ..." -f yellow
            $args = @('shell', 'getprop', 'ro.product.model')
            & "$adb"  $args
            $productModel = (& "$adb"  $args)
            if ([string]::IsNullOrEmpty($productModel))
            {
                Write-Host "Phone is not connected or more than one device is connected" -f red
                & "$adb" devices
                CheckPhoneConnection -deviceMode $deviceMode
            }
            else
            {
                $hardware = (& $adb shell getprop ro.hardware)
                $buildFingerprint = (& $adb shell getprop ro.build.fingerprint)
                Write-Host  "$('Product Model'.PadRight(25)) = $productModel"
                Write-Host  "$('Hardware'.PadRight(25)) = $hardware"
                Write-Host  "$('Current Build'.PadRight(25)) = $buildFingerprint"
                if ($hardware -ne "$phoneModel")
                {
                    Write-Host "ERROR: The wrong phone is connected" -f red
                    CheckPhoneConnection -deviceMode $deviceMode
                }
                else
                {
                    Write-Host "Phone connection is good" -f DarkGreen
                }
            }
        }
    }
    else
    {
        CheckPhoneConnection -deviceMode $deviceMode
    }
}


#-----------------------------------------------------------------------------
#                            ConfirmYesNo Function
#-----------------------------------------------------------------------------
function ConfirmYesNo($title, $message, $defaultChoice = 0)
{
    if ($lessPrompts)
    {
        Write-Host "  [lessPrompt] option is selected: Bypassing Prompt ..." -f DarkGray
        return 0
    }
    else
    {
        $yes = New-Object System.Management.Automation.Host.ChoiceDescription "&Yes", `
            "Accepts the action."

        $no = New-Object System.Management.Automation.Host.ChoiceDescription "&No", `
            "Aborts the process."

        $options = [System.Management.Automation.Host.ChoiceDescription[]]($yes, $no)

        $result = $host.ui.PromptForChoice($title, $message, $options, $defaultChoice)
        return $result
    }
}


#=============================================================================
#                                   MAIN
#=============================================================================
#-------------
ShowDisclaimer
#-------------

#------
# Usage
#------
if ($help)
{
    Test-ScriptFileInfo -Path ".\$($MyInvocation.MyCommand.Name)"
    Get-Help $MyInvocation.InvocationName | Out-String
    Exit
}

#------------------------------------------
# get script path and invocation parameters
#------------------------------------------
$dtmStart = Get-Date
$cwd = (Get-Item -Path ".\" -Verbose).FullName
$scriptPath = $PSScriptRoot
$env:path += ";."

$commandLine = "$($MyInvocation.MyCommand.Name) "
Write-Host "$commandLine " -NoNewline -f 'red' -b 'yellow'
foreach ($key in $PSBoundParameters.Keys)
{
    Write-Host ("-$($key) $($PSBoundParameters[$key]) ") -NoNewline -f 'black' -b 'yellow'
    $commandLine += "-$($key) $($PSBoundParameters[$key]) "
}
Write-Host ""
Write-Host ""
Write-Host  "$('cwd'.PadRight(25)) = $cwd"
Write-Host  "$('scriptPath'.PadRight(25)) = $scriptPath"

#--------------------------------------
# Make sure dependencies are installed.
#--------------------------------------
Write-Host "  Looking for platform-tools ..." -f DarkGray
ValidateDependencies
if (! [string]::IsNullOrEmpty($sdk))
{
    $adb = "$sdk/adb.exe"
    $fastboot = "$sdk/fastboot.exe"
}
else
{
    $adb = "adb"
    $fastboot = "fastboot"
}

#----------------------------------------------------
# Identify Factory Image file and make sure it exists
#----------------------------------------------------
if ([string]::IsNullOrEmpty($factoryFile))
{
    $factoryFile = "$($phoneModel)-*.zip"
    Write-Host "  Assuming Factory File to be $factoryFile" -f DarkGray
}
Write-Host "  Looking for $factoryFile File" -f DarkGray
$factoryFileName = (dir $factoryFile).Name
if ($factoryFile -eq "$($phoneModel)-*.zip")
{
    $factoryFile = $factoryFileName
}
if (-not (Test-Path -Path $factoryFile))
{
    Write-Host "ERROR: Factory Image file [$factoryFile] is NOT Found." -f red
    Write-Host "Aborting ..."
    Exit 1
}
Write-Host  "$('factoryFile'.PadRight(25)) = $factoryFile"

#------------------------
# unzip the Factory Image
#------------------------
Write-Host "  Unzipping Factory Image [$factoryFile]" -f DarkGray
Expand-Archive -Force $factoryFile -DestinationPath .

#----------------------------------------
# Let's see if we got the unzipped folder
#----------------------------------------
$unzippedFolder = "$($phoneModel)-*"
Write-Host "  Looking for $unzippedFolder Folder ..." -f DarkGray
$unzippedFolder = (Get-ChildItem $unzippedFolder -directory).Name
if (-not (Test-Path -Path $unzippedFolder))
{
    Write-Host "ERROR: Could not find Unzipped folder [$unzippedFolder]" -f red
    Write-Host "Aborting ..."
    Exit 1
}
Write-Host  "$('unzippedFolder'.PadRight(25)) = $unzippedFolder"

#------------------------------------------------------
# Let's see if we got the image-$($phoneModel) zip file
#------------------------------------------------------
$imageZip = "image-$($phoneModel)-*.zip"
Write-Host "  Looking for $imageZip file ..." -f DarkGray
$imageZip = (Get-ChildItem "$unzippedFolder/$imageZip" -file).Name
if (-not (Test-Path -Path $unzippedFolder/$imageZip))
{
    Write-Host "ERROR: Could not find image-$($phoneModel)-*.zip [$imageZip]" -f red
    Write-Host "Aborting ..."
    Exit 1
}
$imageZip = "$unzippedFolder/$imageZip"
Write-Host  "$('imageZip'.PadRight(25)) = $imageZip"

#-------------------
# unzip the imageZip
#-------------------
Write-Host "  Unzipping Image [$imageZip] ..." -f DarkGray
Expand-Archive -Force $imageZip -DestinationPath "$unzippedFolder/image_unzipped"

#------------------------
# check and copy boot.img
#------------------------
if (-not (Test-Path -Path "$unzippedFolder/image_unzipped/boot.img"))
{
    Write-Host "ERROR: Could not find Unzipped folder [$unzippedFolder]" -f red
    Write-Host "Aborting ..."
    Exit 1
}
else
{
    Write-Host "  Making a copy of boot.img ..." -f DarkGray
    Copy-Item -Path "$unzippedFolder/image_unzipped/boot.img" -Destination "boot.img"
}

#--------------------
# Delete flash-all.sh
#--------------------
DeleteFile "$unzippedFolder/flash-all.sh"

#--------------------
# Delete flash-base.sh
#--------------------
DeleteFile "$unzippedFolder/flash-base.sh"

#--------------------
# Delete image Zip
#--------------------
DeleteFile "$imageZip"

#--------------------
# Patch flash-all.bat
#--------------------
Write-Host "  Patching flash-all.bat file to remove -w ..." -f DarkGray
$content = Get-Content -Path "$unzippedFolder/flash-all.bat"
$newContent = $content -replace 'fastboot -w update', 'fastboot update'
$newContent | Set-Content -Path "$unzippedFolder/flash-all.bat"

#-------------------------------------
# Transfer stock boot.img to the phone
#-------------------------------------
Write-Host "Warning: If you answer yes to the next question." -f yellow
Write-Host "         The following files will be deleted from your phone." -f yellow
Write-Host "         $transferPath/boot.img" -f yellow
Write-Host "         $transferPath/magisk_patched-*.img" -f yellow
$response = ConfirmYesNo('Do you want to transfer stock boot.img to the phone?', "It will be copied to: $transferPath")
if ($response -eq 0)
{
    CheckPhoneConnection
    # Delete boot.img
    Write-Host "  Deleting $transferPath/boot.img ..." -f DarkGray
    & $adb shell rm -f $transferPath/boot.img

    # Make sure boot.img is deleted
    Write-Host "  Making sure $transferPath/boot.img is deleted ..." -f DarkGray
    $check = (& $adb shell ls -l $transferPath/boot.img)
    if (! [string]::IsNullOrEmpty($check))
    {
        Write-Host "ERROR: $transferPath/boot.img could not be deleted." -f red
        Write-Host "Aborting ..."
        Exit 1
    }

    # Delete magisk_patched-*.img
    Write-Host "  Deleting $transferPath/magisk_patched-*.img ..." -f DarkGray
    & $adb shell rm -f $transferPath/magisk_patched-*.img

    # Make sure magisk_patched-*.img is deleted
    Write-Host "  Making sure magisk_patched-*.img is deleted ..." -f DarkGray
    $check = (& $adb shell ls -l magisk_patched-*.img)
    if (! [string]::IsNullOrEmpty($check))
    {
        Write-Host "ERROR: magisk_patched-*.img could not be deleted." -f red
        Write-Host "Aborting ..."
        Exit 1
    }

    # push boot.img to phone
    Write-Host "  Pushing $transferPath/boot.img ..." -f DarkGray
    & $adb push boot.img $transferPath/boot.img
}
else
{
    Write-Host "Aborted!" -f red
    Exit 1
}

#---------------------------
# See if Magisk is installed
#---------------------------
Write-Host "  Checking to see if Magisk is installed [$magisk] ..." -f DarkGray
$magiskInstalled = (& $adb shell pm list packages $magisk)
if ([string]::IsNullOrEmpty($magiskInstalled))
{
    Write-Host "WARNING: Magisk [$magisk] is not found on the phone" -f yellow
    Write-Host "         This could be either because it is hidden, or it is not installed" -f yellow
    Write-Host "         if it is hidden, optionally you can specify the package name with -m parameter" -f yellow
    Write-Host "         to avoid launching it manually" -f yellow
    Write-Host "Please Launch Magisk manually now." -f red
    Read-Host -Prompt "Press any key to continue"
}
else
{
    # Try to Launch Magisk
    Write-Host "  Launching Magisk [$magisk] ..." -f DarkGray
    & $adb shell monkey -p $magisk -c android.intent.category.LAUNCHER 1
}

#----------------------------
# Display a message and pause
#----------------------------
Write-Host
Write-Host "=====================================================================================" -f yellow
Write-Host "Magisk should now be running on your phone." -f yellow
Write-Host "If it is not, you probably should abort as that could be a sign of issues." -f yellow
Write-Host "Otherwise Please patch boot.img found in the following path:" -f yellow
Write-Host "$transferPath" -f yellow
Write-Host
Write-Host "Please make sure the magisk-patched file is in the following path:" -f yellow
Write-Host "$transferPath" -f yellow
Write-Host
Write-Host "When completed, come back here to continue" -f yellow
Write-Host "CTRL+C to abort" -f yellow
Write-Host "=====================================================================================" -f yellow
Write-Host
Write-Host "If you need guidance about using magisk to patch boot.img check this excellent thread"
Write-Host "https://forum.xda-developers.com/t/guide-root-pixel-6-android-12-with-magisk.4388733/" -f blue
Write-Host
Read-Host -Prompt "Press any key to continue"

#------------------------------------------
# Delete old patched_boot file if it exists
#------------------------------------------
if (Test-Path "patched_boot.img")
{
    Write-Host "  Deleting old patched_boot.img file ..." -f DarkGray
    Remove-Item -Force "patched_boot.img"
}

#---------------------------------
# Copy patched boot.img from phone
#---------------------------------
$response = ConfirmYesNo('Do you want to copy patched boot.img from the phone?', "It will be copied locally")
if ($response -eq 0)
{
    CheckPhoneConnection
    $patchedBoot = (& $adb shell ls  $transferPath/magisk_patched-*.img)
    if ([string]::IsNullOrEmpty($patchedBoot))
    {
        Write-Host "ERROR: magisk_patched-*.img is not found on the phone"
    }
    else
    {
        & $adb pull $patchedBoot patched_boot.img
    }
}
else
{
    Write-Host "Aborted!" -f red
    Exit 1
}
if (-not (Test-Path -Path "patched_boot.img"))
{
    Write-Host "ERROR: patched_boot.img is NOT Found." -f red
    $response = ConfirmYesNo('Do you want to try one last time?', "Last chance")
    if ($response -eq 0)
    {
        CheckPhoneConnection
        $patchedBoot = (& $adb shell ls  $transferPath/magisk_patched-*.img)
        if ([string]::IsNullOrEmpty($patchedBoot))
        {
            Write-Host "ERROR: magisk_patched-*.img is not found on the phone"
        }
        else
        {
            & $adb pull $patchedBoot patched_boot.img
        }
    }
    else
    {
        Write-Host "Aborted!" -f red
        Exit 1
    }
    if (-not (Test-Path -Path "patched_boot.img"))
    {
        Write-Host "ERROR: patched_boot.img is NOT Found." -f red
        Write-Host "Aborting ..."
        Exit 1
    }
}

#---------------------------------------------
# Replace stock boot.img with patched boot.img
# First delete the stock boot.img
#---------------------------------------------
if (Test-Path "$unzippedFolder/image_unzipped/boot.img")
{
    Write-Host "  Deleting stock boot.img file [$unzippedFolder/image_unzipped/boot.img] ..." -f DarkGray
    Remove-Item -Force "$unzippedFolder/image_unzipped/boot.img"
}
# Test to make sure it is deleted.
if (Test-Path "$unzippedFolder/image_unzipped/boot.img")
{
    Write-Host "ERROR: Encountered a problem while deleting [$unzippedFolder/image_unzipped/boot.img]" -f red
    Write-Host "Aborting ..."
    Exit 1
}
# Copy patched boot.img
Write-Host "  Replacing boot.img with patched copy of boot.img ..." -f DarkGray
Copy-Item -Path "patched_boot.img" -Destination "$unzippedFolder/image_unzipped/boot.img"
# test to make sure boot.img exists
if (-not (Test-Path "$unzippedFolder/image_unzipped/boot.img"))
{
    Write-Host "ERROR: Encountered a problem while copying patched_boot.img to [$unzippedFolder/image_unzipped/boot.img]" -f red
    Write-Host "Aborting ..."
    Exit 1
}

#----------------
# Create zip file
#----------------
Write-Host "  Repackaging $imageZip ..." -f DarkGray
Push-Location "$unzippedFolder/image_unzipped"
$args = @('a', '-tzip', '-mx=1', "../../$imageZip")
& "$zip"  $args
Pop-Location

#------------------------------
# Reboot to Bootloader and Wait
#------------------------------
$response = ConfirmYesNo('Do you want to reboot the phone into bootloader mode', "and pause?")
if ($response -eq 0)
{
    Write-Host "  Rebooting into bootloader mode ..." -f DarkGray
    & $adb reboot bootloader
}
else
{
    Write-Host "Aborted!" -f red
    Exit 1
}
if ($lessPrompts)
{
    Start-Sleep -s 5
}
else
{
    Read-Host -Prompt "Press any key to continue"
}

#------------------
# Run flash_all.bat
#------------------
$response = ConfirmYesNo -title "Do you want to run flash_all.bat" -message "and update the phone?" -defaultChoice 1
if ($response -eq 0)
{
    CheckPhoneConnection -deviceMode "fastboot"
    $response = ConfirmYesNo -title "Sorry for Asking again, are you really sure you want to run flash_all.bat" -message "and update the phone?" -defaultChoice 1
    if ($response -eq 0)
    {
        # At this point flash_all.bat will be executed and the phone updated
        Write-Host "Changing current Directory to: $unzippedFolder ..." -f DarkGreen
        Push-Location "$unzippedFolder"
        Write-Host "Executing flash_all.bat ..." -f DarkGreen
        & "./flash-all.bat"
        Pop-Location
    }
    else
    {
        Write-Host "Aborted!" -f red
        Exit 1
    }
}
else
{
    Write-Host "Aborted!" -f red
    Exit 1
}


#----------
# All Done!
#----------
Write-Host ""
Write-Host "Done!" -f DarkGreen
$dtmEnd = Get-Date
$elapsedTime = ($dtmEnd - $dtmStart)
Write-Host ("PixelFlasher Total Elapsed Time: ", $elapsedTime)
Write-Host
