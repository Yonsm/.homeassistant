# Home Assistant Extras for Yonsm

这是我个人的 Home Assistant 扩展和配置，请酌情参考。

# 一、[智家面板](https://github.com/Yonsm/ZhiDash)

[ZhiDash](https://github.com/Yonsm/ZhiDash) 是一个轻量的前端操作面板。


# 二、[智家组件](modules) 

## [ZhiAct](https://github.com/Yonsm/ZhiAct)

根据传感器数值区间来自动控制设备。

## [ZhiBot](https://github.com/Yonsm/ZhiBot)

通用交互式机器人平台，目前支持天猫精灵、小爱同学、钉钉群机器人等。其中钉钉机器人依赖 [ZhiMsg](https://github.com/Yonsm/ZhiMsg)。

## [ZhiCaiYun](https://github.com/Yonsm/ZhiCaiYun)

彩云天气的标准天气插件，支持15天预报。

## [ZhiMi](https://github.com/Yonsm/ZhiMi)

小米云控制的接口，被 `ZhiMsg` 依赖。

## [ZhiModBus](https://github.com/Yonsm/ZhiModBus)

通用 ModBus 空调插件，比 HA 官方做的更通用、更好。

## [ZhiMrBond](https://github.com/Yonsm/ZhiMrBond)

邦先生晾衣架 M1 组件。

## [ZhiMsg](https://github.com/Yonsm/ZhiMsg)

通用消息平台，目前支持钉钉群、小爱同学。依赖 [ZhiMi](https://github.com/Yonsm/ZhiMi)。

## [ZhiSaswell](https://github.com/Yonsm/ZhiSaswell)

SasWell 温控面板组件（地暖）。

## [ZhiViomi](https://github.com/Yonsm/ZhiViomi)

云米洗衣机组件。


# 三、[自定义组件](custom_components) 

**注意：命名为 `***2.py` 是因为和 HA 官方的插件命名冲突或者派生而来**

## [mqtt2/swicth](custom_components/mqtt2/switch.py)

基于 mqtt swicth 扩展的 MQTT 开关，支持以下功能：

- 支持 icon_template 配置，可以使用 Jinja 脚本运算出不同的图标（参考我的 configuration.yaml 中的 mqtt2 Speaker）；
- 支持 original_state attribute。

## [broadlink2/cover](custom_components/broadlink2/cover.py)

基于 broadlink 万能遥控器的窗帘插件（支持 RF），详情请参考 [https://bbs.hassbian.com/thread-1924-1-1.html](https://bbs.hassbian.com/thread-1924-1-1.html)

`这个并非我原创，我只是使用者`，我的修改点：

-   依赖库升级到 `broadlink==0.9.0`，解决 N1 armbian HA 0.8x 下面 segment fault 的问题；
-   `self._travel == 0` 改成 `self._travel <= 0` 避免相关 BUG。


# 四、个人配置

## [configuration.yaml](configuration.yaml)

这是我的 Home Assistant 配置文件。

## [customize.yaml](customize.yaml)

这是我的 Home Assistant 个性化配置文件，主要是中文名称和部分插件的个性化扩展配置。

## [groups.yaml](groups.yaml)

这是我的 Home Assistant 分组文件。

## [automations](automations)

这是我的 Home Assistant 自动化文件，其中有些脚本可以参考，如只用 Motion Sensor [解决洗手间自动开关灯](automations/washroom.yaml)的难题。


# 五、其它 [extras](extras)

## [homeassistant](extras/homeassistant)

对 homeassistant 的小修改，解决部分错误、警告、不优雅等困扰问题。

## [deprecated](extras/deprecated)

一些过期的或者不用的文件，仅供备忘参考。

## [setup](extras/setup)

树莓派和斐讯 N1 armbian 下安装 Home Assistant 的脚本，仅供参考，请按需逐步执行，不要整个脚本直接运行。

## [test](extras/test)

部分测试脚本备忘。
