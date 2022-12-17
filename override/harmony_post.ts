/**
 * scripting object to a sound column... Allow object oriented object interaction with sound sequence.
 * In Harmony, this object is created by the global scripting interface column.getSoundColumn(
 * columnName );
 * In Storyboard, this object is created by the scripting interface SoundTrackManager.getSoundColumn(
 * columnName );
 * It includes methods to iterate over the sound column content. At this moment, it cannot do any
 * modification to the sound column.
 * {@link https://docs.toonboom.com/help/storyboard-pro-7/storyboard/scripting/reference/classsoundColumnInterface.html}
 */
 declare class soundColumnInterface extends QObject {
  /**
   * @returns {string}
   */
  public column(): string;

  /**
   * @returns {soundSequenceInterface[]}
   */
  public sequences(): soundSequenceInterface[];

  /**
   * @returns {string}
   */
  // /* Invalid - Duplicate property name */ column: string;
}

/**
 *
 * {@link https://docs.toonboom.com/help/storyboard-pro-7/storyboard/scripting/reference/classsoundSequenceInterface.html}
 */
declare class soundSequenceInterface extends QObject {
  /**
   * @param {int} startFrame
   * @param {int} endFrame
   * @param {float} startTime
   * @param {float} stopTime
   * @param {string} name
   * @param {string} filename
   * @returns {void}
   */
  constructor(
    startFrame: int,
    endFrame: int,
    startTime: float,
    stopTime: float,
    name: string,
    filename: string
  );

  /**
   * path resolved filename
   * @returns {string}
   */
  public filename(): string;

  /**
   * named of this sound sequence - derived from the filename
   * @returns {string}
   */
  public name(): string;

  /**
   * returns the start frame of this sound sequence, 1 based.
   * @returns {int}
   */
  public startFrame(): int;

  /**
   * returns the start time in second from the beginning of the sound file. The start time is sync with
   * ths start frame.
   * @returns {float}
   */
  public startTime(): float;

  /**
   * returns the stop frame of this sound sequence, value is 1 based
   * @returns {int}
   */
  public stopFrame(): int;

  /**
   * returns the stop time in second. sound will stop playing when reaching either the stop time or the
   * stop frame, whichever comes first
   * @returns {float}
   */
  public stopTime(): float;

  /**
   * @returns {int}
   */
  public stopFrame(): int;

  /**
   * @returns {int}
   */
  public startFrame(): int;

  /**
   * @returns {string}
   */
  // /* Invalid - Duplicate property name */ filename: string;

  /**
   * @returns {string}
   */
  // /* Invalid - Duplicate property name */ name: string;

  /**
   * @returns {float}
   */
  // /* Invalid - Duplicate property name */ startTime: float;

  /**
   * @returns {float}
   */
  // /* Invalid - Duplicate property name */ stopTime: float;
}


declare class MC_DragContext extends QObject {}

/**
 * Helpful custom interfaces below
 */
 
 /**
  * Column Type as returned by column.type()
  */
 declare type ColumnType = "DRAWING" | "SOUND" | "3DPATH" | "BEZIER" | "EASE" | "EXPR" | "TIMING" | "QUATERNION" | "QUATERNIONPATH" | "ANNOTATION";
 
 /**
  * Type name as returned by Attribute.typeName()
  */
 declare type AttrValueType =
   | "ALIAS"
   | "ARRAY_POSITION_2D"
   | "ARRAY_STRING"
   | "BOOL"
   | "COLOR"
   | "COMPATIBILITY"
   | "CUSTOM_NAME"
   | "DOUBLE"
   | "DOUBLEVB"
   | "DRAWING"
   | "ELEMENT"
   | "ENABLE"
   | "FILE_EDITOR"
   | "FILE_LIBRARY"
   | "GENERIC_ENUM"
   | "HSL"
   | "HUE_RANGE"
   | "INT"
   | "LOCKED"
   | "PATH_3D"
   | "POINT_2D"
   | "POSITION_2D"
   | "POSITION_3D"
   | "PUSH_BUTTON"
   | "QUATERNION_PATH"
   | "ROTATION_3D"
   | "SCALE_3D"
   | "SIMPLE_BEZIER"
   | "STRING"
   | "TIMING";