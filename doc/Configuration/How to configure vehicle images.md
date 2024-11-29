# How to configure vehicle images

> [!IMPORTANT]
> When using your own Anki cars (that are not pre-configured / no matching images exist), you must configure the images to be used in the ui's.

You can add and use your own vehicle images for displaying vehicles on the car map as well as in the driver ui.

## Add and configure images for your own real anki cars
The assignment of images to the Anki vehicles is done via the MAC address of the vehicles.
This can be determined through the StaffUi.
There, found or connected vehicles are displayed.

To display a matching image of the vehicle in the DriverUi, a corresponding image in <strong>.webp</strong> format must exist in the directory [src\UserInterface\static\images\Real_Vehicles](../../src\UserInterface\static\images\Real_Vehicles).
The name of the image must match the MAC address (without colons ":").

> [!NOTE]
> Example:  
> MAC address of a vehicle: CE:27:5C:6C:64:6C -> corresponding image: CE275C6C646C.webp

For the standard Anki vehicles (red and blue), appropriate images are provided, which can be copied and renamed.
Instructions on how to convert .png or .jpeg images to .webp images can be found here.
To ensure that the correct images are used on the virtual track as well, the images to be used must be stored in the configuration.
How this works is explained in the following section.

## Add and configure images for your virtual race
The images to be used on the virtual track can be configured via the [config_file.json](../../src/config_file.json).
In the virtual_cars_pics section, the images are assigned to the vehicles.
The images must exist in the directory [src\UserInterface\static\images\Virtual_Vehicles](../../src\UserInterface\static\images\Virtual_Vehicles).
It is recommended to use top-down views of the vehicles.
For real vehicles, the assignment is done via the MAC address of the vehicle.

> [!NOTE]
> Example:
> "CE:27:5C:6C:64:6C": "CE275C6C646C.svg"

For virtual vehicles, the assignment is done via the ID for the vehicle (Virtual Vehicle x, with x as an integer >0). 

> [!NOTE]
> Example: 
> "Virtual Vehicle 1": "VirtualVehicle1.svg"

In both cases, the name of the image file can be arbitrary, and the format is not specified.
However, the image must have a transparent background.
For the standard Anki cars (red and blue), images are also provided here, which can be used as follows:

> [!NOTE]
> Example: 
> "D1:FF:AF:51:CB:30": "blue.svg",
> "Virtual Vehicle 1": "red.svg"

Any number of real and virtual vehicles can be configured.
