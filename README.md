# Text editor
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![MySQL](https://img.shields.io/badge/mysql-%2300f.svg?style=for-the-badge&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

*Python MIPT 2023*

> Author
>> Lukashev Kirill

## Description

This project was written as part of the Python course at MIPT.

Functionality:
 - Add password
 - Change data
 - Removing a password over time

## System requirements

> Python 3 \
> MySQL \
> Docker

## Project build

#### *Сreate virtual environment*
```console
User@user-laptop:~$ pip install virtualenv
User@user-laptop:~$ virtualenv myvenv
User@user-laptop:~$ source myvenv\bin\activate
```
#### *Install requirements.txt*
```console
(myvenv)User@user-laptop:~$ pip install requirements.txt
```
#### *Run command*

```console
(myvenv)User@user-laptop:~$ python3 main.py
(myvenv)User@user-laptop:~$ cd PasswordManager
(myvenv)User@user-laptop:~$ chmod +x install.sh
(myvenv)User@user-laptop:~$ sudo ./install
```

Before running you should create MySQL server

Run from folder, there you cloned repo.

__api_key__ - api key of your bot

__host__ - MySQL host

__user__ - MySQL user

__password__ - MySQL password

__database__ - MySQL database name
```
./run.sh api_key host user password database
```
