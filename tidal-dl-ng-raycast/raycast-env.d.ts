/// <reference types="@raycast/api">

/* 🚧 🚧 🚧
 * This file is auto-generated from the extension's manifest.
 * Do not modify manually. Instead, update the `package.json` file.
 * 🚧 🚧 🚧 */

/* eslint-disable @typescript-eslint/ban-types */

type ExtensionPreferences = {
  /** Execution Mode - Run tidal-dl-ng locally or on a remote server via SSH */
  "executionMode": "local" | "remote",
  /** Remote Host - SSH server hostname or IP address */
  "remoteHost"?: string,
  /** SSH Port - SSH server port */
  "remotePort": string,
  /** SSH Username - Username for SSH connection */
  "remoteUser"?: string,
  /** SSH Key Path - Path to SSH private key file */
  "sshKeyPath"?: string,
  /** SSH Password - Password for SSH connection (if not using key) */
  "sshPassword"?: string
}

/** Preferences accessible in all the extension's commands */
declare type Preferences = ExtensionPreferences

declare namespace Preferences {
  /** Preferences accessible in the `dl` command */
  export type Dl = ExtensionPreferences & {}
  /** Preferences accessible in the `dl-favorites` command */
  export type DlFavorites = ExtensionPreferences & {}
  /** Preferences accessible in the `config` command */
  export type Config = ExtensionPreferences & {}
}

declare namespace Arguments {
  /** Arguments passed to the `dl` command */
  export type Dl = {
  /** Tidal URL */
  "url": string
}
  /** Arguments passed to the `dl-favorites` command */
  export type DlFavorites = {}
  /** Arguments passed to the `config` command */
  export type Config = {}
}

