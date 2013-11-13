#include <Python.h>

// Begin Private Cocoa API
typedef enum _CGSDebugOptions {
    kCGSDebugOptionNone,
    kCGSDebugOptionNoShadows = 16384
} CGSDebugOptions;

extern void CGSGetDebugOptions(CGSDebugOptions *options);
extern void CGSSetDebugOptions(CGSDebugOptions options);
// End Private Cocoa API

static PyObject* toggle_shadows(PyObject * self, PyObject * args) {
    // Begin Private Cocoa Methods
    CGSDebugOptions options;
    CGSGetDebugOptions(&options);
    options ^= kCGSDebugOptionNoShadows;
    CGSSetDebugOptions(options);
 	// End Private Cocoa Methods
    
    return Py_None;
}
 
static PyMethodDef methods[] = {
	{"toggle_shadows", (PyCFunction) toggle_shadows, METH_NOARGS, "toggle_shadows()\n\nTurn system shadows on or off."},
	{NULL, NULL, 0, NULL}
};
 
PyMODINIT_FUNC
init_shadows(void) {
    (void) Py_InitModule3("wm._shadows", methods, "Extension module that allows toggling OS X shadows on and off.");
}
