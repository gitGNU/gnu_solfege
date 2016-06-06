/* GNU Solfege - ear training for GNOME
 * Copyright (C) 2001 Joe Lee
 *
 * Ported to gcc by Steve Lee
 * Ported to Python 3.4 by Tom Cato Amundsen <tca@gnu.org>
 *
 * This program is free software; you can redistribute it and/or modify
 *it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin ST, Fifth Floor, Boston, MA  02110-1301  USA
 */

#include <windows.h>
#include <windowsx.h>
#include <mmsystem.h>
#include <Python.h>
#include "structmember.h"

#define MAX_MIDI_BLOCK_SIZE 1024

#define UNUSED(x) ((void)x)	/* for unreferenced parameters */

enum {
	BLOCK_WRITING = 0,
	BLOCK_READY,
	BLOCK_PLAYING,
	BLOCK_PLAYED 
};

struct tag_MidiBlock {
	MIDIHDR m_header;
	int m_blockState;
	struct tag_MidiBlock* m_next;
};
typedef struct tag_MidiBlock MidiBlockNode;


typedef struct {
    PyObject_HEAD
	HMIDISTRM m_midiOut;
	MidiBlockNode *m_list;
	MidiBlockNode *m_playNode;
	MidiBlockNode *m_listEnd;
} Winmidi;


static void s_SetMidiError(const char *reason, UINT val) {
	UINT retVal;
	char errBuffer[MAXERRORLENGTH];

	retVal = midiOutGetErrorText(val, errBuffer, MAXERRORLENGTH);
	if(retVal == MMSYSERR_NOERROR) {
	/* Returned OK.  Do nothing. */

	} else if(retVal == MMSYSERR_BADERRNUM) {
	sprintf(errBuffer, "Unrecognized MIDI error occurred (%d).", val);

	} else if(retVal == MMSYSERR_INVALPARAM) {
	sprintf(errBuffer, "Invalid error parameter found while retrieving error %d.", val);

	} else {
	sprintf(errBuffer, "Unknown error occurred while retrieving error %d.", val);
	}

	(void)PyErr_Format(PyExc_RuntimeError, "MIDI error encountered while %s: %s", reason, errBuffer);
}


static void FAR PASCAL s_MidiCallback(HMIDISTRM hms, UINT uMsg, DWORD dwUser, DWORD dw1, DWORD dw2) {
	Winmidi *obj = (Winmidi *) dwUser;
	int retVal;

	UNUSED(hms);
	UNUSED(dw1);
	UNUSED(dw2);

	assert(obj);

	/* Only process Done messages. */
	if(uMsg != MOM_DONE) {
	return;
	}

	while(obj->m_playNode) {
	/* Clear the playing flag. */
	obj->m_playNode->m_blockState = BLOCK_PLAYED;

	/* Play the next block, if available. */
	obj->m_playNode = obj->m_playNode->m_next;
	if(obj->m_playNode) {
		/* Check to see if we have exhausted the ready blocks. */
		if(obj->m_playNode->m_blockState != BLOCK_READY) {
		return;
		}

		obj->m_playNode->m_blockState = BLOCK_PLAYING;

		retVal = midiStreamOut(obj->m_midiOut, &obj->m_playNode->m_header,
			sizeof(obj->m_playNode->m_header));
		if(retVal == MMSYSERR_NOERROR) {
		return;
		} else {
		fprintf(stderr, "Error occurred while advancing MIDI block pointer.\n");
		}
	} else {
		retVal = midiStreamPause(obj->m_midiOut);
		if(retVal != MMSYSERR_NOERROR) {
		fprintf(stderr, "Error occurred while pausing MIDI playback.");
		}
		return;
	}
	}
}


static int s_PrepareBlockNodes(Winmidi *obj) {
	UINT retVal;
	MidiBlockNode *node;
	MidiBlockNode *firstReady = 0;

	assert(obj);

	/* Go through the list and prepare all written blocks. */
	node = obj->m_list;
	while(node) {
	if(node->m_blockState == BLOCK_WRITING) {
		if(!firstReady) {
		firstReady = node;
		}

		retVal = midiOutPrepareHeader((HMIDIOUT)obj->m_midiOut,
			&node->m_header,
			sizeof(node->m_header));
		if(retVal != MMSYSERR_NOERROR) {
		s_SetMidiError("preparing header", retVal);
		return 0;
		}

		node->m_blockState = BLOCK_READY;
	}
	node = node->m_next;
	}

	/* If we actually prepared some blocks for playing, queue the first
	 * one. */
	if(!obj->m_playNode && firstReady) {
	obj->m_playNode = firstReady;
	(void)midiStreamOut(obj->m_midiOut, &firstReady->m_header,
		sizeof(firstReady->m_header));
	}

	retVal = midiStreamRestart(obj->m_midiOut);
	if(retVal != MMSYSERR_NOERROR) {
	s_SetMidiError("restarting MIDI stream", retVal);
	return 0;
	}

	return 1;
}


static int s_CleanUpBlockNodes(Winmidi *obj) {
	UINT retVal;
	MidiBlockNode *node, *nextNode;

	assert(obj);

	node = obj->m_list;
	while(node) {
	nextNode = node->m_next;
	if(node->m_blockState == BLOCK_PLAYED) {
		obj->m_list = node->m_next;
		if(node == obj->m_listEnd) {
		obj->m_listEnd = 0;
		}

		/* Dispose of the block. */
		retVal = midiOutUnprepareHeader((HMIDIOUT)obj->m_midiOut, &node->m_header,
			sizeof(node->m_header));
		if(retVal != MMSYSERR_NOERROR) {
		s_SetMidiError("unpreparing header", retVal);
		return 0;
		} else {
		(void)GlobalFreePtr(node->m_header.lpData);
		free(node);
		}
	}
	node = nextNode;
	}

	return 1;
}


static int s_FreeNodes(Winmidi *obj) {
	MidiBlockNode *node, *nextNode;

	assert(obj);

	node = obj->m_list;
	while(node) {
	nextNode = node->m_next;
	obj->m_list = node->m_next;
	if(node == obj->m_listEnd) {
		obj->m_listEnd = 0;
	}

	/* Dispose of the block. */
	(void)GlobalFreePtr(node->m_header.lpData);
	free(node);

	node = nextNode;
	}

	return 1;
}


int s_ResetMidiStream(Winmidi *obj, UINT devNum) {
	UINT retVal;

	assert(obj);

	(void)midiOutReset((HMIDIOUT)obj->m_midiOut);
	if(!s_CleanUpBlockNodes(obj)) {
	return 0;
	}
	(void)midiStreamClose(obj->m_midiOut);
	if(!s_FreeNodes(obj)) {
	return 0;
	}

	retVal = midiStreamOpen(&(obj->m_midiOut), &devNum, 1,
		(DWORD) s_MidiCallback, (DWORD) obj, CALLBACK_FUNCTION); //lint !e620
	if(retVal != MMSYSERR_NOERROR) {
	s_SetMidiError("opening a MIDI stream", retVal);
	return 0;
	}
	assert(obj->m_midiOut);
	
	return 1;
}


static int s_SetUpNewBlock(Winmidi *obj) {
	MidiBlockNode *node;

	assert(obj);
	node = malloc(sizeof(MidiBlockNode));
	if(!node) {
	PyErr_SetString(PyExc_RuntimeError,
		"Out of memory while allocating MIDI block.");
	return 0;
	}

	/* Allocate MIDI buffer memory. */
	memset(node, 0, sizeof(MidiBlockNode));
	node->m_header.lpData = GlobalAllocPtr(GMEM_MOVEABLE | GMEM_SHARE,
		MAX_MIDI_BLOCK_SIZE);
	if(!node->m_header.lpData) {
	PyErr_SetString(PyExc_RuntimeError,
		"Out of memory while allocating MIDI block.");
	free(node);
	return 0;
	}
	node->m_header.dwBufferLength = MAX_MIDI_BLOCK_SIZE;
	node->m_blockState = BLOCK_WRITING;

	/* Place new block at end of the list. */
	if(!obj->m_listEnd) {
	assert(!obj->m_list);
	obj->m_listEnd = node;
	obj->m_list = node;
	} else {
	obj->m_listEnd->m_next = node;
	obj->m_listEnd = node;
	}

	return 1;
}


static MIDIEVENT *s_PrepWriteBlock(Winmidi *obj, int size) {
	MidiBlockNode *node;
	MIDIEVENT *midiEvent;
	assert(obj);

	node = obj->m_listEnd;
	if(!node) {
	/* If there are no blocks in the list, get a new one. */
	if(!s_SetUpNewBlock(obj)) {
		return 0;
	}

	} else if(node->m_blockState != BLOCK_WRITING) {
	/* If the last block is not a writing block, get a new one.*/
	if(!s_SetUpNewBlock(obj)) {
		return 0;
	}

	} else if(node->m_header.dwBytesRecorded + size * sizeof(DWORD) >
		node->m_header.dwBufferLength) {
	/* If there's not enough room in the last block, get a new one. */ 
	if(!s_SetUpNewBlock(obj)) {
		return 0;
	}
	}

	/* We're OK for writing. */
	node = obj->m_listEnd;
	assert(node);
	assert(node->m_blockState == BLOCK_WRITING);
	midiEvent =
	(MIDIEVENT *) (node->m_header.lpData + node->m_header.dwBytesRecorded);
	node->m_header.dwBytesRecorded += size * sizeof(DWORD);

	return midiEvent;
}


static PyObject *s_output_devices(PyObject *self, PyObject *args) {
	MIDIOUTCAPS caps;
	UINT		numDevs, i;
	PyObject    *result;
	
	result = PyList_New(0);
	numDevs = midiOutGetNumDevs();
	if (midiOutGetDevCaps(MIDI_MAPPER, &caps, sizeof(caps)) == 0)
		PyList_Append(result, PyUnicode_FromString(caps.szPname));
	else
		PyList_Append(result, Py_None);		
	for(i = 0; i < numDevs; i++) {
		if (midiOutGetDevCaps(i, &caps, sizeof(caps)) == 0)
			PyList_Append(result, PyUnicode_FromString(caps.szPname));
		else
			PyList_Append(result, Py_None);		
	}
	return result;
}

static void
Winmidi_dealloc(Winmidi* self)
{
    int retVal;
    Py_TYPE(self)->tp_free((PyObject*)self);
    retVal = midiStreamClose(self->m_midiOut);
    if (retVal == MMSYSERR_INVALHANDLE) {
	printf("midiSreamClose: MMSYSERR_INVALHANDLE\n");
    }
}

static PyObject *
Winmidi_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	UINT		retVal;
	UINT		numDevs;
	UINT		devNum;
    Winmidi *self;
    if(!PyArg_ParseTuple(args, "i:Winmidi", &devNum)) {
	return NULL;
    }

    self = (Winmidi *)type->tp_alloc(type, 0);
    if (self != NULL) {
	self->m_midiOut = 0;
	self->m_playNode = 0;
	self->m_list = 0;
	self->m_listEnd = 0;
	/* Get the number of MIDI devices on the system. */
	numDevs = midiOutGetNumDevs();
	if(numDevs == 0) {
	    PyErr_SetString(PyExc_RuntimeError, 
    		"No MIDI output devices found.");
	    Py_DECREF(self);
	    return NULL;
	}
	/* Open the MIDI output device. */
	self->m_midiOut = 0;
	printf("B %i\n", devNum);
	retVal = midiStreamOpen(&(self->m_midiOut), &devNum, 1,
		(DWORD) s_MidiCallback, (DWORD) self, CALLBACK_FUNCTION); //lint !e620
	printf("C %i\n", devNum);
	if(retVal != MMSYSERR_NOERROR) {
		s_SetMidiError("opening a MIDI stream", retVal);
		Py_DECREF(self);
		return NULL;
	}
	assert(self->m_midiOut);

    }

    return (PyObject *)self;
}

static int
Winmidi_init(Winmidi *self, PyObject *args, PyObject *kwds)
{
    return 0;
}


static PyMemberDef Winmidi_members[] = {
    {NULL}  /* Sentinel */
};


static PyObject *Winmidi_NoteOn(PyObject *self, PyObject *args) {
	int delta, channel, note, vel;
	Winmidi *obj;
	MIDIEVENT *evt;

	if(!PyArg_ParseTuple(args, "iiii:note_on", &delta, &channel,
		&note, &vel)) {
	return NULL;
	}
	if(channel < 0 || channel >= 16) {
	PyErr_SetString(PyExc_RuntimeError, "channel out of range");
	return NULL;
	}
	if(note < 0 || note >= 128) {
	PyErr_SetString(PyExc_RuntimeError, "note out of range");
	return NULL;
	}
	if(vel < 0 || vel >= 128) {
	PyErr_SetString(PyExc_RuntimeError, "vel out of range");
	return NULL;
	}
	obj = (Winmidi *) self;
	if(!obj) {
	PyErr_SetString(PyExc_RuntimeError, "invalid Winmidi object");
	return NULL;
	}

	/* printf("Note on:  %d %d %d %d\n", delta, channel, note, vel); */
	evt = s_PrepWriteBlock(obj, 3);
	if(!evt) {
	return NULL;
	}
	evt->dwDeltaTime = (DWORD)delta;
	evt->dwStreamID = 0;
	evt->dwEvent = ((MEVT_SHORTMSG) << 24) +
	(((DWORD)vel) << 16) +
	(((DWORD)note) << 8) +
	(((DWORD)channel + 0x90U));

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *Winmidi_NoteOff(PyObject *self, PyObject *args) {
	int delta, channel, note, vel;
	Winmidi *obj;
	MIDIEVENT *evt;

	if(!PyArg_ParseTuple(args, "iiii:note_off", &delta, &channel,
		&note, &vel)) {
	return NULL;
	}
	if(channel < 0 || channel >= 16) {
	PyErr_SetString(PyExc_RuntimeError, "channel out of range");
	return NULL;
	}
	if(note < 0 || note >= 128) {
	PyErr_SetString(PyExc_RuntimeError, "note out of range");
	return NULL;
	}
	if(vel < 0 || vel >= 128) {
	PyErr_SetString(PyExc_RuntimeError, "vel out of range");
	return NULL;
	}
	obj = (Winmidi *) self;
	if(!obj) {
	PyErr_SetString(PyExc_RuntimeError, "invalid Winmidi object");
	return NULL;
	}

	/* printf("Note off: %d %d %d %d\n", delta, channel, note, vel); */
	evt = s_PrepWriteBlock(obj, 3);
	if(!evt) {
	return NULL;
	}
	evt->dwDeltaTime = (DWORD)delta;
	evt->dwStreamID = 0;
	evt->dwEvent = ((MEVT_SHORTMSG) << 24) +
	(((DWORD)vel) << 16) +
	(((DWORD)note) << 8) +
	(((DWORD)channel + 0x80U));

	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject *Winmidi_ProgramChange(PyObject *self, PyObject *args) {
	int channel, program;
	Winmidi *obj;
	MIDIEVENT *evt;

	if(!PyArg_ParseTuple(args, "ii:program_change", &channel, &program)) {
	return NULL;
	}
	if(channel < 0 || channel >= 16) {
	PyErr_SetString(PyExc_RuntimeError, "channel out of range");
	return NULL;
	}
	if(program < 0 || program >= 128) {
	PyErr_SetString(PyExc_RuntimeError, "program out of range");
	return NULL;
	}
	obj = (Winmidi *) self;
	if(!obj) {
	PyErr_SetString(PyExc_RuntimeError, "invalid Winmidi object");
	return NULL;
	}

	/* printf("Program change: %d %d\n", channel, program); */
	evt = s_PrepWriteBlock(obj, 3);
	if(!evt) {
	return NULL;
	}
	evt->dwDeltaTime = 0;
	evt->dwStreamID = 0;
	evt->dwEvent = ((MEVT_SHORTMSG) << 24) +
	(((DWORD)program) << 8U) +
	(((DWORD)channel + 0xc0U));

	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject *Winmidi_SetTempo(PyObject *self, PyObject *args) {
	int tempo;
	Winmidi *obj;
	MIDIEVENT *evt;

	if(!PyArg_ParseTuple(args, "i:set_tempo", &tempo)) {
	return NULL;
	}
	if((unsigned int) tempo >= (unsigned int) (1 << 24)) {
	PyErr_SetString(PyExc_RuntimeError, "tempo out of range");
	return NULL;
	}
	obj = (Winmidi *) self;
	if(!obj) {
	PyErr_SetString(PyExc_RuntimeError, "invalid Winmidi object");
	return NULL;
	}

	/* printf("Tempo: %d\n", tempo); */
	evt = s_PrepWriteBlock(obj, 3);
	if(!evt) {
	return NULL;
	}
	evt->dwDeltaTime = 0;
	evt->dwStreamID = 0;
	evt->dwEvent = ((MEVT_TEMPO) << 24) +
	(tempo);


	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject *Winmidi_Play(PyObject *self, PyObject *args) {
	Winmidi *obj;
	
	if(!PyArg_ParseTuple(args, ":play")) {
	return NULL;
	}
	obj = (Winmidi *) self;
	if(!obj) {
	PyErr_SetString(PyExc_RuntimeError, "invalid Winmidi object");
	return NULL;
	}

	/* printf("Play called.\n"); */
	if(!s_CleanUpBlockNodes(obj)) {
	return NULL;
	}
	if(!s_PrepareBlockNodes(obj)) {
	return NULL;
	}		

	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject *Winmidi_Reset(PyObject *self, PyObject *args) {
	Winmidi *obj;
	UINT devNum;
	
	if(!PyArg_ParseTuple(args, "i:reset", &devNum)) {
	return NULL;
	}
	obj = (Winmidi *) self;
	if(!obj) {
	PyErr_SetString(PyExc_RuntimeError, "invalid Winmidi object");
	return NULL;
	}

	if(!s_ResetMidiStream(obj, devNum)) {
	return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef Winmidi_methods[] = {
    {"note_on", (PyCFunction)Winmidi_NoteOn, METH_VARARGS, ""},
    {"note_off", (PyCFunction)Winmidi_NoteOff, METH_VARARGS, ""},
    {"program_change", (PyCFunction)Winmidi_ProgramChange, METH_VARARGS, ""},
    {"set_tempo", (PyCFunction)Winmidi_SetTempo, METH_VARARGS, ""},
    {"play", (PyCFunction)Winmidi_Play, METH_VARARGS, ""},
    {"reset", (PyCFunction)Winmidi_Reset, METH_VARARGS, ""},
    {"output_devices", s_output_devices,    METH_NOARGS, NULL},
    {NULL}  /* Sentinel */
};

static PyTypeObject WinmidiType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "winmidi.Winmidi",             /* tp_name */
    sizeof(Winmidi),             /* tp_basicsize */
    0,                         /* tp_itemsize */
    (destructor)Winmidi_dealloc, /* tp_dealloc */
    0,                         /* tp_print */
    0,                         /* tp_getattr */
    0,                         /* tp_setattr */
    0,                         /* tp_reserved */
    0,                         /* tp_repr */
    0,                         /* tp_as_number */
    0,                         /* tp_as_sequence */
    0,                         /* tp_as_mapping */
    0,                         /* tp_hash  */
    0,                         /* tp_call */
    0,                         /* tp_str */
    0,                         /* tp_getattro */
    0,                         /* tp_setattro */
    0,                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT |
        Py_TPFLAGS_BASETYPE,   /* tp_flags */
    "Winmidi objects",           /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    Winmidi_methods,             /* tp_methods */
    Winmidi_members,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Winmidi_init,      /* tp_init */
    0,                         /* tp_alloc */
    Winmidi_new,                 /* tp_new */
};

static PyModuleDef winmidimodule = {
    PyModuleDef_HEAD_INIT,
    "winmidi",
    "Example module that creates an extension type.",
    -1,
    Winmidi_methods,
    NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC
PyInit_winmidi(void)
{
    PyObject* m;

    if (PyType_Ready(&WinmidiType) < 0)
        return NULL;

    m = PyModule_Create(&winmidimodule);
    if (m == NULL)
        return NULL;

    Py_INCREF(&WinmidiType);
    PyModule_AddObject(m, "Winmidi", (PyObject *)&WinmidiType);
    return m;
}
