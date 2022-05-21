#!/usr/bin/python
# Be sure to run this as root!
import subprocess

def runcmd(command, timeout):
        command = command + " & pid=$!;sleep " + str(timeout) + "; kill -9 $pid"
        #print(command)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        return process.stdout.read()

result = runcmd('hcidump', 5)
print(result)
