from django.shortcuts import render

def index(request):
    return render(request, "ide/index.html")

def python_ide(request):
    return render(request, "ide/python-ide.html")

def java_ide(request):
    return render(request, "ide/java-ide.html")
