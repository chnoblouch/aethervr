# AetherVR Guide

This guide explains how to configure and use AetherVR.

## Configuration

AetherVR has a few parameters that can be configured in the panel on the left-hand side.

### Camera

You can configure which camera AetherVR should use for video capture and which resolution is preferred. It is recommended to use low resolutions because processing large frames reduces performance even though it increases tracking precision slightly.

### Max. Frames per Second

This is the maximum number of camera frames that can be processed per second. Reducing this number increases performance but might also cause input lag.

### Headset Pitch/Yaw Deadzones

This is the minimum angle you need to turn your head to make the virtual headset start rotating. If this is number is too low, you might accidentally rotate the headset through small head movements, but if it is too high, you have to turn your head an uncomfortable amount to control the headset.

### Controller Rotation

You can apply an additional 3D rotation to your virtual controllers so they point in the right direction when your hands are upright.

### Gestures

AetherVR maps hand gestures to virtual controller button and thumbstick interactions. When a gesture is recognized, the color of the camera overlay changes to indicate which one was detected. The recognized gestures are:

| Gesture      | Description                                                                                             | Color   |
| ------------ | ------------------------------------------------------------------------------------------------------- | ------- |
| Pinch        | Holding thumb and index finger together                                                                 | Yellow  |
| Palm Pinch   | Like pinch, but with your palm facing yourself                                                          | Magenta |
| Fist         |                                                                                                         | Blue    |
| Middle Pinch | Holding thumb and middle finger together and moving them horizontally to control the virtual thumbstick | Cyan    |

### Press Thumbstick During Use

Some applications only register controller thumbstick movements when the thumbstick is pressed. Turn this option on to press the virtual thumbstick when performing the middle pinch gesture.
