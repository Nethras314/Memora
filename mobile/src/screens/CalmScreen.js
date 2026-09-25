import React, { useState } from 'react';
import { View } from 'react-native';
import ExerciseScreen from './ExerciseScreen';
import SleepScreen from './SleepScreen';
import { BigButton } from '../components/ui';

export default function CalmScreen() {
  const [mode, setMode] = useState('breathe');

  return (
    <View style={{ flex: 1 }}>
      <View style={{ flexDirection: 'row', gap: 10, paddingHorizontal: 20, paddingTop: 16 }}>
        <View style={{ flex: 1 }}>
          <BigButton title="🌿 Breathe" variant={mode === 'breathe' ? 'primary' : 'outline'} onPress={() => setMode('breathe')} />
        </View>
        <View style={{ flex: 1 }}>
          <BigButton title="🌙 Sleep" variant={mode === 'sleep' ? 'primary' : 'outline'} onPress={() => setMode('sleep')} />
        </View>
      </View>
      {mode === 'breathe' ? <ExerciseScreen /> : <SleepScreen />}
    </View>
  );
}
