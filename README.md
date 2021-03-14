# Home Assistant Extras for Yonsm

这是我个人的 Home Assistant 扩展和配置，请酌情参考。

## 一、[智家面板](https://github.com/Yonsm/ZhiDash)

[ZhiDash](https://github.com/Yonsm/ZhiDash) 是一个轻量的前端操作面板。

## 二、[智家组件](https://github.com/Yonsm/.homeassistant/tree/main/modules)

### 1. [ZhiAct](https://github.com/Yonsm/ZhiAct)

根据传感器数值区间来自动控制设备。

### 2. [ZhiBot](https://github.com/Yonsm/ZhiBot)

通用交互式机器人平台，目前支持天猫精灵、小爱同学、钉钉群机器人等。其中钉钉机器人依赖 [ZhiMsg](https://github.com/Yonsm/ZhiMsg)。

### 3. [ZhiCaiYun](https://github.com/Yonsm/ZhiCaiYun)

彩云天气的标准天气插件，支持 15 天预报。

### 4. [ZhiMi](https://github.com/Yonsm/ZhiMi)

小米云控制的接口，被 `ZhiMsg` 依赖。

### 5. [ZhiModBus](https://github.com/Yonsm/ZhiModBus)

通用 ModBus 空调插件，比 HA 官方做的更通用、更好。

### 6. [ZhiMQTT](https://github.com/Yonsm/ZhiMQTT)

基于 MQTT Swicth 的扩展开关。

### 7. [ZhiMrBond](https://github.com/Yonsm/ZhiMrBond)

邦先生晾衣架 M1 组件。

### 8. [ZhiMsg](https://github.com/Yonsm/ZhiMsg)

通用消息平台，目前支持钉钉群、小爱同学。依赖 [ZhiMi](https://github.com/Yonsm/ZhiMi)。

### 9. [ZhiRemote](https://github.com/Yonsm/ZhiRemote)

基于 `Broadlink` 万能遥控器的窗帘插件。

### 10. [ZhiSaswell](https://github.com/Yonsm/ZhiSaswell)

SasWell 温控面板组件（地暖）。

### 11. [ZhiViomi](https://github.com/Yonsm/ZhiViomi)

云米洗衣机组件。

## 三、个人配置

### 1. [configuration.yaml](https://github.com/Yonsm/.homeassistant/tree/main/configuration.yaml)

这是我的 Home Assistant 配置文件。

### 2. [customize.yaml](https://github.com/Yonsm/.homeassistant/tree/main/customize.yaml)

这是我的 Home Assistant 个性化配置文件，主要是中文名称和部分插件的个性化扩展配置。

### 3. [automations](https://github.com/Yonsm/.homeassistant/tree/main/automations)

这是我的 Home Assistant 自动化文件，其中有些脚本可以参考，如只用 Motion Sensor [解决洗手间自动开关灯](automations/washroom.yaml)的难题。

## 四、其它 [extras](https://github.com/Yonsm/.homeassistant/tree/main/extras)

### 1. [homeassistant](https://github.com/Yonsm/.homeassistant/tree/main/extras/homeassistant)

对 homeassistant 的小修改，解决部分错误、警告、不优雅等困扰问题。

### 2. [deprecated](https://github.com/Yonsm/.homeassistant/tree/main/extras/deprecated)

一些过期的或者不用的文件，仅供备忘参考。

### 3. [setup](https://github.com/Yonsm/.homeassistant/tree/main/extras/setup)

树莓派和斐讯 N1 armbian 下安装 Home Assistant 的脚本，仅供参考，请按需逐步执行，不要整个脚本直接运行。

### 4. [test](https://github.com/Yonsm/.homeassistant/tree/main/extras/test)

部分测试脚本备忘。
