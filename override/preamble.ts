/// <reference path="../../shared/qtscript.d.ts" />

/**
 * Undocumented types (FIXME)
 */
declare class BAPP_SpecialFolders {}
declare class GlobalObject {}
declare class QScriptable {}
declare class SCRIPT_QSWidget extends QWidget {}
declare class Labeled extends QWidget {}
declare class MO_SignalEmitter extends QWidget {}
declare class SCR_AbstractInterface {}
declare type QScriptContext = any;
declare type QScriptEngine = any;
declare type QScriptValue = any;
declare type DD_DragObject = any;
declare class UI_DialogController {}

/**
 * The path to the current .js file being run.
 * @example
 * var currentFilePath = __file__; Result: /path/to/file.js
 */
declare var __file__: string;

/**
 * The name of the current .js file being run.
 * @example
 * var currentFileName = __FILE__; Result: file.js
 */
declare var __FILE__: string;
