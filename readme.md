# 一、功能说明

1. 批量创建/删除云主机
2. 可指定是否同时删除公网ip和数据盘
3. 查询停机状态主机
4. 删除停机状态主机

# 二、环境准备

## 1. 安装python3

### 1.1. centos7.4

yum install python36

键入python3 --version有输出

```
Python 3.x.x
```

### 1.2. ubuntu16

默认是3.x.x，不需要额外安装

## 2. 安装Python SDK

 安装请参考: https://docs.jdcloud.com/cn/sdk/python
 
### 2.1. 安装pip3

```
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

### 2.2. 安装Python SDK

```
pip3 install -U jdcloud_sdk
```

## 3. 将压缩包拷贝到linux系统中

## 4. 解压

```
unzip vmoperate.zip
```

# 三、脚本使用

## 1. 配置文件

### 1.1. conf.json

配置详细说明请参考: https://docs.jdcloud.com/cn/virtual-machines/api/createinstances

1. 修改accessKey，secretKey
2. regionId: 创建主机的地域ID(https://docs.jdcloud.com/cn/common-declaration/api/introduction)
3. maxCount: 购买云主机的数量；取值范围：[1,100]，默认为1
4. az: 云主机所属的可用区。(https://docs.jdcloud.com/cn/common-declaration/api/introduction)
5. instanceType: 实例规格。可查询DescribeInstanceTypes接口获得指定地域或可用区的规格信息。(https://docs.jdcloud.com/cn/virtual-machines/api/describeinstancetypes)
6. password: 云主机密码
7. imageId: 镜像id
8. systemDisk: 系统盘配置
    autoDelete: 是否随云主机一起删除，即删除主机时是否自动删除此磁盘，默认为true，本地盘(local)不能更改此值。
9. dataDisks: 数据盘配置，不需要可去掉
10. primaryNetworkInterface: 主网卡配置
    subnetId: 子网id
    securityGroups: 安全组
11. elasticIp: 弹性公网ip配置，如果没有需要可去掉

### 1.2 delete.json

autoDeleteFloatIp: 删除云主机时，是否同时删除公网ip
autoDeleteDataDisk: 删除云主机时，是否同时删除数据盘，如果conf.json中，数据盘的autoDelete设置都为true，建议把这个参数设为false

### 1.3 stop.json

结构同delete.json文件相同，用于执行qstop命令后，将delete.json文件中，停机状态的云主机id保存到此文件中

## 2. 创建云主机

**注意：**

创建云主机时，如果数据盘参数的autoDelete设为true，则该数据盘会随着主机释放而释放

执行命令: 
```
python3 createInstance.py create
```

## 3. 删除云主机

**注意:**

1. 删除云主机时，如果指定delete.json文件中，autoDeleteFloatIp和autoDeleteDataDisk值为true，表示同时删除绑定的公网ip和数据盘
2. 此命令会删除所有在delete.json文件列表中的云主机，删除完成后，delete.json文件清空。

```
python3 createInstance.py delete
```

## 4. 查询delete.json列表中关机状态的云主机

**注意:**

该命令会查询出delete.json文件中，停机状态的云主机，并将停机主机的id保存到stop.json文件中，同时将这些主机id从delete.json文件中移除

```
python3 createInstance.py qstop
```

## 5. 删除停机状态云主机

**注意:**

该命令会删除stop.json文件中的所有云主机，删除完成后会清空stop.json文件。

```
python3 createInstance.py qdelete
```
