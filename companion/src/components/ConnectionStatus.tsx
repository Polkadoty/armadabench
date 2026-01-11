/**
 * ConnectionStatus - Displays Star Forge connection status
 */

import { Wifi, WifiOff } from 'lucide-react';
import type { FleetStatePayload } from '@/lib/postMessageProtocol';

interface ConnectionStatusProps {
  isConnected: boolean;
  fleetState: FleetStatePayload | null;
}

export function ConnectionStatus({ isConnected, fleetState }: ConnectionStatusProps) {
  return (
    <div className={`flex items-center gap-2 px-3 py-2 text-xs border-b ${
      isConnected ? 'bg-green-50 dark:bg-green-950/30' : 'bg-yellow-50 dark:bg-yellow-950/30'
    }`}>
      {isConnected ? (
        <>
          <Wifi className="h-3 w-3 text-green-600 dark:text-green-400" />
          <span className="text-green-700 dark:text-green-300">
            Connected to Star Forge
          </span>
          {fleetState && (
            <span className="ml-auto text-muted-foreground">
              {fleetState.faction || 'No faction'} • {fleetState.points.total}/{fleetState.pointsLimit} pts
            </span>
          )}
        </>
      ) : (
        <>
          <WifiOff className="h-3 w-3 text-yellow-600 dark:text-yellow-400" />
          <span className="text-yellow-700 dark:text-yellow-300">
            Not connected - Open from Star Forge
          </span>
        </>
      )}
    </div>
  );
}
