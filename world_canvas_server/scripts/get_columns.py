#!/usr/bin/env python

import rospy
import yaml
import uuid
import copy
import unique_id
import world_canvas_msgs.msg
import world_canvas_msgs.srv

from geometry_msgs.msg import *
from rospy_message_converter import message_converter
from yocs_msgs.msg import Column, ColumnList
from visualization_msgs.msg import Marker, MarkerArray
from world_canvas_utils.serialization import *


def publish(anns, data):
    column_list = ColumnList()
    marker_list = MarkerArray()    

    marker_id = 1
    for a, d in zip(anns, data):
        
        # Columns
        object = deserializeMsg(d.data, Column)
        column_list.obstacles.append(object)
        
        # Markers
        marker = Marker()
        marker.id = marker_id
        marker.header = a.pose.header
        marker.type = a.shape
        marker.ns = "column_obstacles"
        marker.action = Marker.ADD
        marker.lifetime = rospy.Duration.from_sec(0)
        marker.pose = copy.deepcopy(a.pose.pose.pose)
        marker.scale = a.size
        marker.color = a.color

        marker_list.markers.append(marker)

        marker_id = marker_id + 1

    marker_pub = rospy.Publisher('column_marker',    MarkerArray, latch=True, queue_size=1)
    column_pub = rospy.Publisher('column_pose_list', ColumnList,  latch=True, queue_size=1)

    column_pub.publish(column_list)
    marker_pub.publish(marker_list)
    
    return


if __name__ == '__main__':
    rospy.init_node('columns_loader')
    world    = rospy.get_param('~world')
    ids      = rospy.get_param('~ids', [])
    names    = rospy.get_param('~names', [])
    types    = rospy.get_param('~types', [])
    keywords = rospy.get_param('~keywords', [])
    related  = rospy.get_param('~relationships', [])

    rospy.loginfo("Waiting for get_annotations service...")
    rospy.wait_for_service('get_annotations')

    rospy.loginfo("Loading annotations for world %s", world)
    get_anns_srv = rospy.ServiceProxy('get_annotations', world_canvas_msgs.srv.GetAnnotations)
    respAnns = get_anns_srv(world,
                           [unique_id.toMsg(uuid.UUID('urn:uuid:' + id)) for id in ids],
                            names, types, keywords,
                           [unique_id.toMsg(uuid.UUID('urn:uuid:' + r)) for r in related])

    if len(respAnns.annotations) > 0:
        rospy.loginfo("Publishing visualization markers for %d retrieved annotations...",
                       len(respAnns.annotations))
    else:
        rospy.loginfo("No annotations found for world %s with the given search criteria", world)
        sys.exit()

    rospy.loginfo("Loading data for the %d retrieved annotations", len(respAnns.annotations))
    get_data_srv = rospy.ServiceProxy('get_annotations_data', world_canvas_msgs.srv.GetAnnotationsData)
    respData = get_data_srv([a.data_id for a in respAnns.annotations])

    if len(respData.data) > 0:
        rospy.loginfo("Publishing data for %d retrieved annotations...", len(respData.data))
        publish(respAnns.annotations, respData.data)
    else:
        rospy.logwarn("No data found for the %d retrieved annotations", len(respAnns.annotations))
        
    rospy.loginfo("Done")
    rospy.spin()
