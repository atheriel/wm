#include <stdio.h>
#include <string.h>
#include <Python.h>

#include "AXError.h"
#include "AXUIElement.h"
#include "AXValue.h"

/*
 * Intended to allow formatted error messages. Format strings work like
 * they do in printf(), etc.
 */
char * formattedMessage(char * format, ...) {
    char buf[1024];
    va_list arglist;
    va_start(arglist, format);
    vsprintf(buf, format, arglist);
    va_end(arglist);
    size_t l = strlen(buf);
    while(l && buf[l-1] =='\n') {
        buf[l-1] = 0;
        l--;
    }
    return strdup(buf);
}

/* ========
    Module API
======== */

// Member classes
typedef struct {
    PyObject_HEAD
    AXUIElementRef _ref;
} AccessibleElement;

// Module functions
static PyObject * is_enabled(PyObject *);
static PyObject * create_application_ref(PyObject *, PyObject *);
static PyObject * create_systemwide_ref(PyObject *, PyObject *);

// Exceptions
PyDoc_STRVAR(InvalidUIElementError_docstring, 
    "Raised when a reference to some AccessibleElement is no longer valid, usually "
    "\nbecause the process is dead.");
static PyObject * InvalidUIElementError;

PyDoc_STRVAR(APIDisabledError_docstring, 
    "Raised when a the Accessibility API is disabled for some reference. Usually this is "
    "\nbecause the user needs to enable Accessibility, although some Apple applications "
    "\nare known to respond with this error regardless.");
static PyObject * APIDisabledError;

/* ========
    Private members
======== */

static PyObject * parseCFTypeRef(const CFTypeRef);
static AccessibleElement * elementWithRef(AXUIElementRef *);
static void handleAXErrors(char *, AXError);


/* ========
    Module Implementation
======== */

// AccessibleElement Class & Class Methods

PyDoc_STRVAR(names_docstring, "names()"
    "\n\nRetrieves a list of attribute names available to this element and the "
    "\nerror (possibly None)."
    "\n\n:rval: A tuple of the names and the error."
    "\n\nExample usage::"
    "\n\n\tattributes, error = element.names()"
    "\n\tif error == None:"
    "\n\t\tfor name in attributes: print name");

static PyObject * names(AccessibleElement * self, PyObject * args) {
    PyObject * result = NULL;
    CFArrayRef names;
    printf("Check.\n");
    AXError error = AXUIElementCopyAttributeNames(self->_ref, &names);
    printf("Check two.\n");
    if (error == kAXErrorSuccess) {
        printf("Check three.\n");
        result = parseCFTypeRef(names);
    } else {
        handleAXErrors("attribute names", error);
    }

    if (names != NULL) CFRelease(names);
    return result;
}

PyDoc_STRVAR(count_docstring, "count(attribute_names)"
    "\n\nReturns the number of values for the specified attribute name(s), possibly zero. "
    "\nIf the element does not possess this/these attribute(s), this method will raise a "
    "\nValueError."
    "\n\n:param attribute_names: Either a single name or a series of names, all strings."
    "\n:rvalue: Either a single value's count or a tuple of the values' counts."
    "\n\n A common usage might look like::"
    "\n\n\ttry:"
    "\n\t\trole_count = element.count('AXRole')"
    "\n\t\tprint 'Count for AXRole: %d and AXRoleDescription: %d' % role_count"
    "\n\texcept ValueError:"
    "\n\t\tprint 'I guess those aren't available...'");

static PyObject * count(AccessibleElement * self, PyObject * args) {
    PyObject * result = Py_None;
    // This allows for retrieving multiple objects, so find how many were
    // requested and loop over them.
    Py_ssize_t attribute_count = PyTuple_Size(args);
    if (attribute_count > 1) {
        result = PyTuple_New(attribute_count);
    }

    for (int i = 0; i < attribute_count; i++) {
        PyObject * name = PyTuple_GetItem(args, (Py_ssize_t) i);
        if (!name) {
            if (attribute_count > 1) Py_DECREF(result);
            return NULL; // PyTuple_GetItem will set an Index error.
        }
        if (PyUnicode_Check(name)) { // Handle Unicode strings
            name = PyUnicode_AsUTF8String(name);
        }
        if (!PyString_Check(name)) {    
            if (attribute_count > 1) Py_DECREF(result);
            PyErr_SetString(PyExc_TypeError, "Non-string attribute names are not permitted.");
            return NULL;
        }
         // Get a string representation of the attribute name
        const char * name_string = PyString_AsString(name);
        if (!name_string) {
            if (attribute_count > 1) Py_DECREF(result);
            PyErr_SetString(PyExc_TypeError, "An unknown error occured while converting string arguments to char *.");
            return NULL;
        }

        // Convert that representation to something Carbon will understand.
        CFStringRef name_strref = CFStringCreateWithCString(kCFAllocatorDefault, name_string, kCFStringEncodingUTF8);
        
        // Get the count itself
        CFIndex count;
        AXError error = AXUIElementGetAttributeValueCount(self->_ref, name_strref, &count);
        
        if (error == kAXErrorSuccess) {
            if (attribute_count > 1) {
                PyTuple_SetItem(result, i, Py_BuildValue("i", count));
            } else {
                result = Py_BuildValue("i", count);
            }
        } else {
            // If any of the requests fail, release memory and raise an exception
            if (attribute_count > 1) Py_DECREF(result);
            if (name_strref != NULL) CFRelease(name_strref);
            handleAXErrors(name_string, error);
            return NULL;
        }
        if (name_strref != NULL) CFRelease(name_strref);
    }
    return result;
}

PyDoc_STRVAR(get_docstring, "get(attribute_names)"
    "\n\nReturns a copy of the values for the specified attribute name(s) and the "
    "\nerror (possibly None). If the element does not possess this attribute, this "
    "\nmethod will raise a ValueError."
    "\n\n:param attribute_names: Either a single name or a series of names, all strings."
    "\n:rval: A tuple of the values and the error."
    "\n\n A common usage might look like::"
    "\n\n\trole, error = element.get('AXRole')"
    "\n\tif error == None: print role"
    "\n\nUsing more than one attribute name::"
    "\n\n\tvalue, error = element.get('AXRole', 'AXRoleDescription')"
    "\n\tif error == None:"
    "\n\t\tprint value[0], value[1]"
    "\n\telse:"
    "\n\t\tprint error"
    "\n\nThe errors themselves are numbers whose exact meaning varies; see the "
    "\nAccessibility API documentation for details.");

static PyObject * get(AccessibleElement * self, PyObject * args) {
    PyObject * result = NULL;
    // This allows for retrieving multiple objects, so find how many were
    // requested and loop over them.
    Py_ssize_t attribute_count = PyTuple_Size(args);
    if (attribute_count > 1) {
        result = PyTuple_New(attribute_count);
    }

    for (int i = 0; i < attribute_count; i++) {
        PyObject * name = PyTuple_GetItem(args, (Py_ssize_t) i);
        if (!name) {
            if (attribute_count > 1) Py_DECREF(result);
            return NULL; // PyTuple_GetItem will set an Index error.
        }
        if (PyUnicode_Check(name)) { // Handle Unicode strings
            name = PyUnicode_AsUTF8String(name);
        }
        if (!PyString_Check(name)) {    
            PyErr_SetString(PyExc_TypeError, "Non-string attribute names are not permitted.");
            if (attribute_count > 1) Py_DECREF(result);
            return NULL;
        }
         // Get a string representation of the attribute name
        const char * name_string = PyString_AsString(name);
        if (!name_string) {
            PyErr_SetString(PyExc_TypeError, "An unknown error occured while converting string arguments to char *.");
            return NULL;
        }

        // Convert that representation to something Carbon will understand.
        CFStringRef name_strref = CFStringCreateWithCString(kCFAllocatorDefault, name_string, kCFStringEncodingUTF8);
        
        // Copy the value
        CFTypeRef value = NULL;
        AXError error = AXUIElementCopyAttributeValue(self->_ref, name_strref, &value);
        
        if (error == kAXErrorSuccess) {
            if (attribute_count > 1) {
                PyTuple_SetItem(result, i, parseCFTypeRef(value));
            } else {
                result = parseCFTypeRef(value);
            }
        } else {
            // If any of the requests fail, release memory and raise an exception
            if (attribute_count > 1) Py_DECREF(result);
            if (name_strref != NULL) CFRelease(name_strref);
            if (value != NULL) CFRelease(value);
            handleAXErrors(name_string, error);
            return NULL;
        }
        if (name_strref != NULL) CFRelease(name_strref);
    }
    return result;
}

PyDoc_STRVAR(set_docstring, "set(attribute_name, value)"
    "\n\nSets the value of the specified attribute (if possible). If the element "
    "\ndoes not possess this attribute or the attribute is not modifiable, this "
    "\nmethod will raise a ValueError."
    "\n\n:param str attribute_name: The name of the attribute to set."
    "\n:param value: The new value of the attribute."
    "\n:rval: The error, or None if no error occurs."
    "\n\nThe errors themselves are numbers whose exact meaning varies; see the "
    "\nAccessibility API documentation for details.");

static PyObject * set(AccessibleElement * self, PyObject * args) {
    PyObject * result = NULL;
    // There should be at least two arguments
    Py_ssize_t attribute_count = PyTuple_Size(args);
    if (attribute_count <= 1) {
        PyErr_SetString(PyExc_ValueError, "Not enough arguments.");
        return NULL;
    }
    // The first argument should be a string
    PyObject * name = PyTuple_GetItem(args, (Py_ssize_t) 0);
    if (!name) {
        return NULL; // PyTuple_GetItem will set an Index error.
    }
    if (PyUnicode_Check(name)) { // Handle Unicode strings
        name = PyUnicode_AsUTF8String(name);
    }
    if (!PyString_Check(name)) {    
        PyErr_SetString(PyExc_TypeError, "Non-string attribute names are not permitted.");
        return NULL;
    }
     // Get a string representation of the attribute name
    const char * name_string = PyString_AsString(name);
    if (!name_string) {
        PyErr_SetString(PyExc_TypeError, "An unknown error occured while converting string arguments to char *.");
        return NULL;
    }

    // Convert that representation to something Carbon will understand.
    CFStringRef name_strref = CFStringCreateWithCString(kCFAllocatorDefault, name_string, kCFStringEncodingUTF8);

    // Check to see if the attribute can be set at all
    Boolean can_set;
    AXError error = AXUIElementIsAttributeSettable(self->_ref, name_strref, &can_set);

    if (error == kAXErrorSuccess && !can_set) {
        PyErr_SetString(PyExc_ValueError, formattedMessage("The %s attribute cannot be modified.", name_string));
        return NULL;
    } else if (error != kAXErrorSuccess) {
        handleAXErrors(name_string, error);
        return result;
    }

    // Try to figure out what to set
    if (CFStringCompare(name_strref, kAXPositionAttribute, 0) == kCFCompareEqualTo) {
        
        // For position, need a tuple of floats
        PyObject * value = PyTuple_GetItem(args, (Py_ssize_t) 1);
        float pair[2];
        if (!PyTuple_Check(value)) {
            PyErr_SetString(PyExc_ValueError, "Setting AXPosition requires a tuple of exactly two floats.");
            return NULL;
        } else if (PyTuple_Size(value) != 2) {
            PyErr_SetString(PyExc_ValueError, "Setting AXPosition requires a tuple of exactly two floats.");
            return NULL;
        } else if (!PyArg_ParseTuple(value, "ff", &pair[0], &pair[1])) {
            PyErr_SetString(PyExc_ValueError, "Setting AXPosition requires a tuple of exactly two floats.");
            return NULL;
        }
        CGPoint pos = CGPointMake((CGFloat) pair[0], (CGFloat) pair[1]);
        CFTypeRef position = (CFTypeRef) AXValueCreate(kAXValueCGPointType, (const void *) &pos);
        AXError error = AXUIElementSetAttributeValue(self->_ref, kAXPositionAttribute, position);

        result = Py_BuildValue("i", error);
        return result;
    } else if (CFStringCompare(name_strref, kAXSizeAttribute, 0) == kCFCompareEqualTo) {
        
        // For size, need a tuple of floats
        PyObject * value = PyTuple_GetItem(args, (Py_ssize_t) 1);
        float pair[2];
        if (!PyTuple_Check(value)) {
            PyErr_SetString(PyExc_ValueError, "Setting AXSize requires a tuple of exactly two floats.");
            return NULL;
        } else if (PyTuple_Size(value) != 2) {
            PyErr_SetString(PyExc_ValueError, "Setting AXSize requires a tuple of exactly two floats.");
            return NULL;
        } else if (!PyArg_ParseTuple(value, "ff", &pair[0], &pair[1])) {
            PyErr_SetString(PyExc_ValueError, "Setting AXSize requires a tuple of exactly two floats.");
            return NULL;
        }
        CGSize s = CGSizeMake((CGFloat) pair[0], (CGFloat) pair[1]);
        CFTypeRef size = (CFTypeRef) AXValueCreate(kAXValueCGSizeType, (const void *) &s);
        AXError error = AXUIElementSetAttributeValue(self->_ref, kAXSizeAttribute, size);

        result = Py_BuildValue("i", error);
        return result;
    }

    PyErr_SetString(PyExc_NotImplementedError, "Incomplete implementation.");
    return result;
}

static PyObject * can_set(AccessibleElement * self, PyObject * args) {
    PyObject * result = NULL;
    Py_ssize_t attribute_count = PyTuple_Size(args);
    if (attribute_count > 1) {
        PyErr_SetString(PyExc_ValueError, "Too many arguments.");
        return NULL;
    }
    // The first argument should be a string
    PyObject * name = PyTuple_GetItem(args, (Py_ssize_t) 0);
    if (!name) {
        return NULL; // PyTuple_GetItem will set an Index error.
    }
    if (PyUnicode_Check(name)) { // Handle Unicode strings
        name = PyUnicode_AsUTF8String(name);
    }
    if (!PyString_Check(name)) {    
        PyErr_SetString(PyExc_TypeError, "Non-string attribute names are not permitted.");
        return NULL;
    }
     // Get a string representation of the attribute name
    const char * name_string = PyString_AsString(name);
    if (!name_string) {
        PyErr_SetString(PyExc_TypeError, "An unknown error occured while converting string arguments to char *.");
        return NULL;
    }

    // Convert that representation to something Carbon will understand.
    CFStringRef name_strref = CFStringCreateWithCString(kCFAllocatorDefault, name_string, kCFStringEncodingUTF8);

    // Check to see if the attribute can be set at all
    Boolean can_set;
    AXError error = AXUIElementIsAttributeSettable(self->_ref, name_strref, &can_set);

    if (error == kAXErrorSuccess) {
        result = can_set ? Py_True : Py_False;
    } else {
        handleAXErrors(name_string, error);
    }

    if (name_strref != NULL) CFRelease(name_strref);
    return result;
}

PyDoc_STRVAR(is_alive_docstring, "is_alive()"
    "\n\nReturns True if the AXUIElementRef is still valid.");

static PyObject * is_alive(AccessibleElement * self, PyObject * args) {
    // Just check to see if the element responds to a basic attribute request
    CFTypeRef value = NULL;
    AXError error = AXUIElementCopyAttributeValue(self->_ref, kAXRoleAttribute, &value);
    if (value != NULL) CFRelease(value);
    
    return (error == kAXErrorInvalidUIElement) ? Py_False : Py_True;
}

static PyMethodDef AccessibleElement_methods[] = {
    {"names", (PyCFunction) names, METH_NOARGS, names_docstring},
    {"get", (PyCFunction) get, METH_VARARGS, get_docstring},
    {"count", (PyCFunction) count, METH_VARARGS, count_docstring},
    {"set", (PyCFunction) set, METH_VARARGS, set_docstring},
    {"can_set", (PyCFunction) can_set, METH_VARARGS, NULL},
    {"is_alive", (PyCFunction) is_alive, METH_NOARGS, is_alive_docstring},
    {NULL, NULL}  /* Sentinel */
};

static PyTypeObject AccessibleElement_type = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "wm._accessibility.AccessibleElement", /*tp_name*/
    sizeof(AccessibleElement), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    0,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,        /*tp_flags*/
    "A basic accessibile element.", /* tp_doc */
    0,                       /* tp_traverse */
    0,                       /* tp_clear */
    0,                       /* tp_richcompare */
    0,                       /* tp_weaklistoffset */
    0,                       /* tp_iter */
    0,                       /* tp_iternext */
    AccessibleElement_methods, /* tp_methods */
};

// Module functions

static PyObject * is_enabled(PyObject * self) {
	return AXAPIEnabled() ? Py_True : Py_False;
}

static PyObject * is_trusted(PyObject * self) {
    return AXIsProcessTrusted() ? Py_True : Py_False;
}

static PyObject * create_application_ref(PyObject * self, PyObject * args) {
    pid_t pid;
 
    if (!PyArg_ParseTuple(args, "i", &pid))
        return NULL;

	AXUIElementRef ref = AXUIElementCreateApplication(pid);
	AccessibleElement * result = elementWithRef(&ref);
 
    return (PyObject *) result;
}

static PyObject * create_systemwide_ref(PyObject * self, PyObject * args) {

    AXUIElementRef ref = AXUIElementCreateSystemWide();
    AccessibleElement * result = elementWithRef(&ref);
 
    return (PyObject *) result;
}

// Module definition
 
static PyMethodDef methods[] = {
	{"is_enabled", (PyCFunction) is_enabled, METH_NOARGS, "is_enabled()\n\nCheck if accessibility has been enabled on the system."},
    {"is_trusted", (PyCFunction) is_trusted, METH_NOARGS, "is_trusted()\n\nCheck if this application is a trusted process."},
	{"create_application_ref", create_application_ref, METH_VARARGS, "Create an accessibile application with the given PID."},
	{"create_systemwide_ref", create_systemwide_ref, METH_VARARGS, "Get a system-wide accessible element reference."},
	{NULL, NULL, 0, NULL}
};
 
PyMODINIT_FUNC
init_accessibility(void) {
	PyObject* m;

    AccessibleElement_type.tp_new = PyType_GenericNew;
    if (PyType_Ready(&AccessibleElement_type) < 0)
    	return;

    m = Py_InitModule3("wm._accessibility", methods, "Extension module that provides access to the Accessibility framework.");

    Py_INCREF(&AccessibleElement_type);
    PyModule_AddObject(m, "AccessibleElement", (PyObject *) &AccessibleElement_type);

    InvalidUIElementError = PyErr_NewExceptionWithDoc("wm._accessibility.InvalidUIElementError", InvalidUIElementError_docstring, PyExc_ValueError, NULL);
    PyModule_AddObject(m, "InvalidUIElementError", InvalidUIElementError);

    APIDisabledError = PyErr_NewExceptionWithDoc("wm._accessibility.APIDisabledError", APIDisabledError_docstring, PyExc_Exception, NULL);
    PyModule_AddObject(m, "APIDisabledError", APIDisabledError);
}

/* ========
    Private Member Implementations
======== */

static AccessibleElement * elementWithRef(AXUIElementRef * ref) {
    AccessibleElement * self;
    self = PyObject_New(AccessibleElement, &AccessibleElement_type);
    if (self == NULL)
        return NULL;
    self->_ref = *ref;
        return self;
}

static PyObject * parseCFTypeRef(const CFTypeRef value) {
    PyObject * result = NULL;
    
    // Check what type the return is
    if (CFGetTypeID(value) == CFStringGetTypeID()) {
        
        // The value is a CFStringRef, so try to decode it to a char *
        CFIndex length = CFStringGetLength(value);
        // printf("String has length: %ld\n", length);
        if (length == 0) { // Empty string
            result = Py_None;
        } else {
            char * buffer = CFStringGetCStringPtr(value, kCFStringEncodingUTF8); // Fast way
            if (!buffer) {
                // Slow way
                CFIndex maxSize = CFStringGetMaximumSizeForEncoding(length, kCFStringEncodingUTF8);
                buffer = (char *) malloc(maxSize);
                if (CFStringGetCString(value, buffer, maxSize, kCFStringEncodingUTF8)) {
                    result = Py_BuildValue("s", buffer);
                } else {
                    PyErr_SetString(PyExc_TypeError, "The referenced string representation could not be parsed.");
                }
            } else {
                result = Py_BuildValue("s", buffer);
            }
        }

    } else if (CFGetTypeID(value) == CFBooleanGetTypeID()) {

        // The value is a boolean, so get its value and return True/False
        if (CFBooleanGetValue(value)) {
            result = Py_True;
        } else {
            result = Py_False;
        }

    } else if (CFGetTypeID(value) == AXUIElementGetTypeID()) {

        // The value is another AXUIElementRef (probably a window...)
        result = (PyObject *) elementWithRef((AXUIElementRef *) &value);

    } else if (CFGetTypeID(value) == AXValueGetTypeID()) {

        // The value is one of the AXValues
        AXValueType value_type = AXValueGetType(value);
        if (value_type == kAXValueCGPointType) {
            
            // It's a point
            CGPoint point;
            if (AXValueGetValue(value, kAXValueCGPointType, (void *) &point)) {
                result = Py_BuildValue("ff", point.x, point.y);
            } else {
                PyErr_SetString(PyExc_ValueError, "The value cannot be retrieved.");
                result = NULL;
            }
        } else if (value_type == kAXValueCGSizeType) {
            
            // It's a size
            CGSize size;
            if (AXValueGetValue(value, kAXValueCGSizeType, (void *) &size)) {
                result = Py_BuildValue("ff", size.width, size.height);
            } else {
                PyErr_SetString(PyExc_ValueError, "The value cannot be retrieved.");
                result = NULL;
            }
        } else if (value_type == kAXValueCGRectType) {
            
            // It's a rect
            PyErr_SetString(PyExc_NotImplementedError, "Not all AXValue can yet be parsed.");
            result = NULL;
        } else {
            
            PyErr_SetString(PyExc_NotImplementedError, "Not all AXValue can yet be parsed.");
            result = NULL;
        }

    } else if (CFGetTypeID(value) == CFArrayGetTypeID()) {

        // An array
        if (CFArrayGetCount(value) <= 0) {
            // Empty array
            result = Py_None;
        } else {
            // It's an array... gonna have to do this recursively...
            Py_ssize_t size = CFArrayGetCount(value);
            PyObject * list = PyList_New(size);
            if (!list) {
                // Shouldn't happen
                PyErr_SetString(PyExc_TypeError, "A list could not be created for the reference.");
            } else {
                for (CFIndex i = 0; i < CFArrayGetCount(value); i++) {
                    PyObject * element = parseCFTypeRef(CFArrayGetValueAtIndex(value, i));
                    PyList_SetItem(list, i, element);
                }
                result = list;
            }
        }
    } else {
        PyErr_SetString(PyExc_TypeError, "Unknown CFTypeRef type.");
    }

    return result;
}

static void handleAXErrors(char * attribute_name, AXError error) {
    printf("Error handler called.\n");
    switch(error) {
        case kAXErrorCannotComplete:
            PyErr_SetString(PyExc_Exception, formattedMessage("The request for %s could not be completed (perhaps the application is not responding?).", attribute_name));
            break;

        case kAXErrorAttributeUnsupported:
            PyErr_SetString(PyExc_ValueError, formattedMessage("This element does not possess the attribute %s.", attribute_name));
            break;

        case kAXErrorIllegalArgument:
            PyErr_SetString(PyExc_ValueError, formattedMessage("Invalid argument. This is probably caused by a faulty AccessibleElement."));
            break;

        case kAXErrorNoValue:
            PyErr_SetString(PyExc_ValueError, formattedMessage("The attribute %s has no value.", attribute_name));
            break;

        case kAXErrorInvalidUIElement:
            PyErr_SetString(InvalidUIElementError, formattedMessage("This element is no longer valid (perhaps the application has been closed?)."));
            break;

        case kAXErrorNotImplemented:
            PyErr_SetString(PyExc_NotImplementedError, formattedMessage("This element does not implement the Accessibility API for the attribute %s.", attribute_name));
            break;

        case kAXErrorAPIDisabled:
            PyErr_SetString(APIDisabledError, formattedMessage("This element does not respond to Accessibility requests -- perhaps Accessibility is not enabled on the system?"));
            break;

        default:
            PyErr_SetString(PyExc_Exception, formattedMessage("Error %ld encountered with attibute %s.", error, attribute_name));
            break;
    }
}
