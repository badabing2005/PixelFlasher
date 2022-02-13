<#
    .SYNOPSIS
        This is a Powershell script is to update a rooted Pixel phone with new factory image and retain root.

    .DESCRIPTION
        This is a Powershell script is to update a rooted Pixel phone with new factory image and retain root.
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
          - Launches Magisk
          - Waits for the user to complete the patch on the phone
              TODO: automate the previous step to magisk patch programatically
          - Transfers patched boot.img to the PC
          - Replaces stock boot.img with patched boot.img
          - Repackages the image zip with patched boot.img
          - Reboots to bootloader and pauses
          - Launches flash_all.bat to update the phone

    .PARAMETER  help
        Alias: h
        Show Usage Help

    .PARAMETER factoryFile
        Alias: f
        Factory image zip file, example: oriole-sq1d.220205.003-factory-a5a63f2a.zip,
        not required if it is in current directory

    .PARAMETER phoneModel
        Alias: p
        Factory image zip file, example: oriole-sq1d.220205.003-factory-a5a63f2a.zip,
        default: oriole

    .PARAMETER transferPath
        Alias: t
        Where stock boot.img file will be copied to (on the phone),
        default: /storage/emulated/0/Download

    .PARAMETER zip
        Alias: z
        Specify path to 7zip.exe,
        default: C:\Program Files\7-Zip\7z.exe,
        not required if it is in the path or current directory

    .PARAMETER sdk
        Alias: s
        Specify path to Android SDK Platform-Tools,
        not required if it is in the path or current directory

    .EXAMPLE
        ./PixelFlasher.ps1
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
    [Alias("s")][string]$sdk = "",
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
    $key = $Host.UI.RawUI.ReadKey()
    Write-Host
    $prompt = [string]$key.Character

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
    $yes = New-Object System.Management.Automation.Host.ChoiceDescription "&Yes", `
        "Accepts the action."

    $no = New-Object System.Management.Automation.Host.ChoiceDescription "&No", `
        "Aborts the process."

    $options = [System.Management.Automation.Host.ChoiceDescription[]]($yes, $no)

    $result = $host.ui.PromptForChoice($title, $message, $options, $defaultChoice)
    return $result
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
    Get-Help $MyInvocation.InvocationName | Out-String
    Exit
}

#------------------------------------------
# get script path and invocation parameters
#------------------------------------------
$cwd = (Get-Item -Path ".\" -Verbose).FullName
$scriptPath = $PSScriptRoot

$commandLine = "$($MyInvocation.MyCommand.Name) "
Write-Host "$commandLine " -NoNewline -f 'Gray' -b 'yellow'
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
$response = ConfirmYesNo('Do you want to transfer stock boot.img to the phone?', "It will be copied to: $transferPath")
if ($response -eq 0)
{
    CheckPhoneConnection
    & $adb push boot.img /storage/emulated/0/Download/boot.img
}
else
{
    Write-Host "Aborted!" -f red
    Exit 1
}

#---------------------
# Try to Launch Magisk
#---------------------
& $adb shell monkey -p com.topjohnwu.magisk -c android.intent.category.LAUNCHER 1

#----------------------------
# Display a message and pause
#----------------------------
Write-Host "------------------------------------------"
Write-Host "Magisk should now be running on your phone"
Write-Host "If it is not, Start magisk on your phone, "
Write-Host "patch boot.img found in Download folder:  "
Write-Host "$transferPath                             "
Write-Host "and then come back here to continue       "
Write-Host "CTRL+C to abort                           "
Write-Host "------------------------------------------"
pause >nul

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
    $patchedBoot = (& $adb shell ls  /storage/emulated/0/Download/magisk_patched-*.img)
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
        $patchedBoot = (& $adb shell ls  /storage/emulated/0/Download/magisk_patched-*.img)
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
    & $adb reboot bootloader
}
else
{
    Write-Host "Aborted!" -f red
    Exit 1
}
pause >nul

#------------------
# Run flash_all.bat
#------------------
$response = ConfirmYesNo -title "Do you want to run flash_all.bat" -message "and update the phone?" -defaultChoice 1
if ($response -eq 0)
{
    CheckPhoneConnection -deviceMode "fastboot"
    $patchedBoot = (& $adb shell ls  /storage/emulated/0/Download/magisk_patched-*.img)
    $response = ConfirmYesNo -title "Sorry for Asking again, are you really sure you want to run flash_all.bat" -message "and update the phone?" -defaultChoice 1
    if ($response -eq 0)
    {
        # At this point flash_all.bat will be executed and the phone updated
        Write-Host "Executing $unzippedFolder/flash_all.bat ..." -f DarkGreen
        & "$unzippedFolder/flash_all.bat"
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
