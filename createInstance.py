#!/usr/bin/python3
import time
import json
import sys
import copy
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.core.logger import Logger
from jdcloud_sdk.services.vm.client.VmClient import VmClient
from jdcloud_sdk.services.vpc.client.VpcClient import VpcClient
from jdcloud_sdk.services.disk.client.DiskClient import DiskClient
from jdcloud_sdk.services.vm.models.InstanceSpec import InstanceSpec
from jdcloud_sdk.services.vm.apis.CreateInstancesRequest import CreateInstancesParameters, CreateInstancesRequest
from jdcloud_sdk.services.vm.apis.DescribeInstanceRequest import DescribeInstanceParameters, DescribeInstanceRequest
from jdcloud_sdk.services.vm.apis.DeleteInstanceRequest import DeleteInstanceParameters, DeleteInstanceRequest
from jdcloud_sdk.services.vpc.apis.DeleteElasticIpRequest import DeleteElasticIpParameters, DeleteElasticIpRequest
from jdcloud_sdk.services.disk.apis.DeleteDiskRequest import DeleteDiskParameters, DeleteDiskRequest
from jdcloud_sdk.services.vm.apis.DescribeInstanceStatusRequest import DescribeInstanceStatusParameters, \
    DescribeInstanceStatusRequest
from jdcloud_sdk.core.config import Config


# 读取配置文件
def readconf(jsonfile):
    with open(jsonfile, 'r') as load_f:
        return json.load(load_f)


# 将主机id追加入delete.json文件，后续删除云主机读取该文件
def writeInDeleteFile(confObj, deleteObj, instanceIds):
    instanceItem = dict()
    instanceItem["regionId"] = confObj["regionId"]
    instanceItem["instanceIds"] = instanceIds["instanceIds"]
    deleteObj["instanceItems"].append(instanceItem)
    with open("delete.json", 'w') as f:
        json.dump(deleteObj, f, indent=4)
        print("delete.json文件更新")


# 恢复配置
def setDefaultForDeleteFile(deleteObj):
    deleteObj["instanceItems"].clear()
    with open("delete.json", 'w') as f:
        json.dump(deleteObj, f, indent=4)


def getVmClient(accessKey, secretKey):
    credential = Credential(accessKey, secretKey)
    logger = Logger(2)
    config = Config(timeout=1000)
    client = VmClient(credential, logger=logger, config=config)
    return client


def getVpcClient(accessKey, secretKey):
    credential = Credential(accessKey, secretKey)
    logger = Logger(2)
    config = Config(timeout=1000)
    client = VpcClient(credential, logger=logger, config=config)
    return client


def getDiskClient(accessKey, secretKey):
    credential = Credential(accessKey, secretKey)
    logger = Logger(2)
    config = Config(timeout=1000)
    client = DiskClient(credential, logger=logger, config=config)
    return client


# 创建实例
def createInstance(confObj, deleteObj):
    client = getVmClient(access_key, secret_key)
    name = None
    az = None
    instanceType = None
    imageId = None
    password = None
    elasticIp = None
    primaryNetworkInterface = None
    systemDisk = None
    dataDisks = None

    instanceSpec = confObj["instanceSpec"]

    if "name" in instanceSpec.keys():
        name = instanceSpec["name"]
    if "az" in instanceSpec.keys():
        az = instanceSpec["az"]
    if "instanceType" in instanceSpec.keys():
        instanceType = instanceSpec["instanceType"]
    if "imageId" in instanceSpec.keys():
        imageId = instanceSpec["imageId"]
    if "password" in instanceSpec.keys():
        password = instanceSpec["password"]
    if "elasticIp" in instanceSpec.keys():
        elasticIp = instanceSpec["elasticIp"]
    if "primaryNetworkInterface" in instanceSpec.keys():
        primaryNetworkInterface = instanceSpec["primaryNetworkInterface"]
    if "systemDisk" in instanceSpec.keys():
        systemDisk = instanceSpec["systemDisk"]
    if "dataDisks" in instanceSpec.keys():
        dataDisks = instanceSpec["dataDisks"]

    instanceSpec = InstanceSpec(
        name=name,
        az=az,
        instanceType=instanceType,
        imageId=imageId,
        password=password,
        elasticIp=elasticIp,
        primaryNetworkInterface=primaryNetworkInterface,
        systemDisk=systemDisk,
        dataDisks=dataDisks
    )

    try:
        parameters = CreateInstancesParameters(regionId=confObj["regionId"], instanceSpec=instanceSpec)
        parameters.setMaxCount(confObj["maxCount"])
        request = CreateInstancesRequest(parameters)
        resp = client.send(request)
        if resp.error is not None:
            print("创建主机实例错误: ", resp.error.code, resp.error.message)
            print("request_id: ", resp.request_id)
            return
        print("创建主机id: ", resp.result)
        writeInDeleteFile(confObj, deleteObj, resp.result)
    except Exception as e:
        print(e)


# 获取待删除主机实例id列表
def getInstanceIdss(deleteObj):
    instanceIdss = dict()
    for instanceItem in deleteObj["instanceItems"]:
        regionId = instanceItem["regionId"]
        if regionId not in instanceIdss.keys():
            instanceIdss[regionId] = []
        for instanceId in instanceItem["instanceIds"]:
            instanceIdss[regionId].append(instanceId)
    return instanceIdss


# 删除实例
def deleteInstance(deleteObj):
    client = getVmClient(access_key, secret_key)

    # 删除云主机实例
    for instanceItem in deleteObj["instanceItems"]:
        regionId = instanceItem["regionId"]
        for instanceId in instanceItem["instanceIds"]:

            try:
                parameters = DeleteInstanceParameters(regionId=regionId, instanceId=instanceId)
                request = DeleteInstanceRequest(parameters)
                resp = client.send(request)
                if resp.error is not None:
                    print("删除主机实例错误: ", resp.error.code, resp.error.message)
                    print("request_id: ", resp.request_id)
                    continue
                print("删除云主机: ", instanceId)
            except Exception as e:
                print(e)


# 判断实例列表中的实例是否都不存在
def judgeInstancesNotExist(instanceIdss):
    for regionId, instanceIds in instanceIdss.items():
        for instanceId in instanceIds:
            if describeInstance(regionId, instanceId):
                return False

    return True


# 获取实例信息
def describeInstance(regionId, instanceId):
    client = getVmClient(access_key, secret_key)
    try:
        parameters = DescribeInstanceParameters(regionId, instanceId)
        request = DescribeInstanceRequest(parameters)
        resp = client.send(request)
        if resp.error is not None:
            return False
        return True
    except Exception as e:
        print(e)


# 获取实例信息
def getInstanceInfo(regionId, instanceId):
    client = getVmClient(access_key, secret_key)
    try:
        parameters = DescribeInstanceParameters(regionId, instanceId)
        request = DescribeInstanceRequest(parameters)
        resp = client.send(request)
        if resp.error is not None:
            print("获取主机信息错误: ", resp.error.code, resp.error.message)
            print("request_id: ", resp.request_id)
            return
        return resp.result
    except Exception as e:
        print(e)


# 获取绑定云主机的ip id
def getFloatIpIds(deleteObj):
    floatIpIds = dict()
    for instanceItem in deleteObj["instanceItems"]:
        regionId = instanceItem["regionId"]
        if regionId not in floatIpIds.keys():
            floatIpIds[regionId] = []
        for instanceId in instanceItem["instanceIds"]:
            instanceInfo = getInstanceInfo(regionId, instanceId)
            floatIpId = getFloatIpId(instanceInfo)
            if floatIpId is not None:
                floatIpIds[regionId].append(floatIpId)
    return floatIpIds


# 获取待删除数据盘id
def getDataDiskIdss(deleteObj):
    dataDiskIdss = dict()
    for instanceItem in deleteObj["instanceItems"]:
        regionId = instanceItem["regionId"]
        if regionId not in dataDiskIdss.keys():
            dataDiskIdss[regionId] = []
        for instanceId in instanceItem["instanceIds"]:
            instanceInfo = getInstanceInfo(regionId, instanceId)
            dataDiskIds = getDataDiskIds(instanceInfo)
            if len(dataDiskIds) > 0:
                dataDiskIdss[regionId].extend(dataDiskIds)
    return dataDiskIdss


# 判断实例是否绑定公网ip，返回公网ip的id
def getFloatIpId(instanceInfo):
    if instanceInfo is not None:
        if "elasticIpId" in instanceInfo["instance"].keys():
            return instanceInfo["instance"]["elasticIpId"]
        else:
            return None


# 删除绑定的公网ip
def deleteFloatIp(regionId, floatIpId):
    client = getVpcClient(access_key, secret_key)
    try:
        parameters = DeleteElasticIpParameters(regionId, floatIpId)
        request = DeleteElasticIpRequest(parameters)
        resp = client.send(request)
        if resp.error is not None:
            print("删除弹性公网ip错误: ", resp.error.code, resp.error.message)
            print("request_id: ", resp.request_id)
            return
    except Exception as e:
        print(e)


# 批量删除公网ip
def deleteFloatIps(deleteObj, floatIpIdss):
    # 判断delete.json中，autoDeleteFloatIp是否为true
    if deleteObj["autoDeleteFloatIp"]:
        for regionId, floatIpIds in floatIpIdss.items():
            for floatIpId in floatIpIds:
                deleteFloatIp(regionId, floatIpId)


# 获取已挂载数据盘id
def getDataDiskIds(instanceInfo):
    diskIds = list()
    if instanceInfo is not None:
        if "dataDisks" in instanceInfo["instance"].keys():
            for dataDisk in instanceInfo["instance"]["dataDisks"]:
                if dataDisk["status"] == "attached":
                    diskIds.append(dataDisk["cloudDisk"]["diskId"])
        return diskIds
    return diskIds


# 删除数据盘
def deleteDataDisk(regionId, diskIds):
    client = getDiskClient(access_key, secret_key)

    for diskId in diskIds:
        try:
            parameters = DeleteDiskParameters(regionId, diskId)
            request = DeleteDiskRequest(parameters)
            resp = client.send(request)
            if resp.error is not None:
                print("删除数据盘错误: ", resp.error.code, resp.error.message)
                print("request_id: ", resp.request_id)
                continue
        except Exception as e:
            print(e)


# 批量删除数据盘
def deleteDataDisks(deleteObj, dataDiskIdss):
    if deleteObj["autoDeleteDataDisk"]:
        for regionId, dataDiskIds in dataDiskIdss.items():
            deleteDataDisk(regionId, dataDiskIds)


# 查询关机状态的主机
# def describeStatusStop(instanceIdss):
#
#     for regionId, instanceIds in instanceIdss.items():
#         instanceIdsTemp = copy.deepcopy(instanceIds)
#         for instanceId in instanceIds:
#             instanceInfo = getInstanceInfo(regionId, instanceId)
#             if instanceInfo is not None:
#                 if instanceInfo["instance"]["status"] != "stopped":
#                     # 将状态不是stopped的主机从列表中移除
#                     instanceIdsTemp.remove(instanceId)
#         instanceIdss[regionId] = instanceIdsTemp
#     return instanceIdss
def describeStatusStop(deleteObj):

    instancesItems = list()

    for instancesItem in deleteObj["instanceItems"]:
        regionId = instancesItem["regionId"]
        instanceIdsTemp = copy.deepcopy(instancesItem["instanceIds"])
        for instanceId in instancesItem["instanceIds"]:
            instanceInfo = getInstanceInfo(regionId, instanceId)
            if instanceInfo is not None:
                if instanceInfo["instance"]["status"] != "stopped":
                    instanceIdsTemp.remove(instanceId)
            else:
                instanceIdsTemp.remove(instanceId)
        instancesItem["instanceIds"] = instanceIdsTemp
        instancesItems.append(instancesItem)
    return instancesItems


def main(confObj, deleteObj):
    if sys.argv[1] == "delete":

        instanceIdss = getInstanceIdss(deleteObj)
        floatIpIdss = getFloatIpIds(deleteObj)
        dataDiskIdss = getDataDiskIdss(deleteObj)

        print("待删除主机id: ", json.dumps(instanceIdss))
        print()
        print("绑定公网ip: ", json.dumps(floatIpIdss))
        print()
        print("绑定数据盘: ", json.dumps(dataDiskIdss))
        print()

        # 删除云主机实例
        print("正在删除云主机...")
        deleteInstance(deleteObj)

        # 判断主机是否已经删除完毕
        while True:
            time.sleep(10)
            if judgeInstancesNotExist(instanceIdss):
                break

        print("云主机删除完成!")

        # 删除绑定的公网ip
        deleteFloatIps(deleteObj, floatIpIdss)

        # 删除绑定数据盘
        deleteDataDisks(deleteObj, dataDiskIdss)

        # 还原delete.json文件
        setDefaultForDeleteFile(deleteObj)
    elif sys.argv[1] == "create":
        createInstance(confObj, deleteObj)
    elif sys.argv[1] == "qstop":
        # instanceIdss = getInstanceIdss(deleteObj)
        # instanceIdssStoppedStatus = describeStatusStop(instanceIdss)
        instanceIdssStoppedStatus = describeStatusStop(deleteObj)
        print("关机状态的主机: ", json.dumps(instanceIdssStoppedStatus))
    else:
        exit("argument error, please choose create or delete")


if __name__ == "__main__":
    confObj = readconf("conf.json")
    deleteObj = readconf("delete.json")
    access_key = confObj["accessKey"]
    secret_key = confObj["secretKey"]
    if len(sys.argv) != 2:
        exit("number of arguments error")
    main(confObj, deleteObj)
