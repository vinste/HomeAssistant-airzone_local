# Airzone Local plugin for Home Assistant

## Introduction

Allow to view & control all your zones register on your Airzone system, using the [local API](https://doc.airzone.es/producto/Gama_AZ6/Airzone/Comunes/Manuales/MI_AZ6_WSCLAPI_A4_MUL.pdf), from [Home Assistant](https://www.home-assistant.io/).

This is a (heavily changed) fork from https://github.com/max13fr/Airzonecloud-HomeAssistant, if you cannot or do not want to use the local api use max13fr integration. 

![Screenshot](screenshot.png)

## Install / upgrade

### Add module

In your home assistant directory (where you have your **configuration.yaml**) :

- create the directory **custom_components** if not already existing
- copy **custom_components/airzone_local** directory from this github repository inside your **custom_components**. In case of upgrade, you can delete the **airzone_local** first then copy the new one.

Finally, you should have the following tree :

- configuration.yaml
- custom_components/
  - airzone_local/
    - \_\_init\_\_.py
    - climate.py
    - manifest.py

### Configure

In your **configuration.yaml** add the following lines :

```
climate:
  - platform: airzone_local
    ip: IP of local airzone server
    scan_interval: 30
    number_of_zones: 6  #number of zones configured in system
    masterid: 1

```
