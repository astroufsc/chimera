<script lang="ts">
	import { onDestroy } from 'svelte';
	import type {
		TelescopeCover,
		TelescopePark,
		TelescopeSlew,
		TelescopeTracking
	} from 'chimera-ws-client';

	import { client } from '$lib/client';
	import EventLog, { type LogEntry } from '$lib/components/EventLog.svelte';
	import { connection } from '$lib/stores/connection.svelte';

	type Scope = TelescopeSlew & TelescopePark & TelescopeTracking & TelescopeCover;

	const telescope = $derived(
		connection.objects.find((o) => o.bases.includes('Telescope')) ?? null
	);
	const has = (capability: string) => telescope?.bases.includes(capability) ?? false;
	const scope = $derived(telescope ? client.get<Scope>(telescope.path) : null);

	let ra = $state<number | null>(null);
	let dec = $state<number | null>(null);
	let alt = $state<number | null>(null);
	let az = $state<number | null>(null);
	let slewing = $state(false);
	let tracking = $state(false);
	let parked = $state(false);
	let coverOpen = $state(false);

	let targetRa = $state('');
	let targetDec = $state('');
	let busy = $state<string | null>(null);
	let failure = $state<string | null>(null);
	let log = $state<LogEntry[]>([]);

	let offs: (() => void)[] = [];
	let pollTimer: ReturnType<typeof setInterval> | null = null;

	// (re)wire polling + events whenever the telescope object appears
	$effect(() => {
		if (!telescope || !scope) return;
		const path = telescope.path;

		const feed =
			(event: string) =>
			(...args: unknown[]) => {
				log.unshift({ ts: Date.now(), path, event, args });
				if (log.length > 500) log.length = 500;
			};
		for (const event of [
			'slew_begin',
			'slew_complete',
			'park_complete',
			'unpark_complete',
			'tracking_started',
			'tracking_stopped'
		]) {
			offs.push(client.on(path, event, feed(event)));
		}

		void poll();
		pollTimer = setInterval(() => void poll(), 1000);
		return teardown;
	});

	function teardown() {
		for (const off of offs) off();
		offs = [];
		if (pollTimer !== null) clearInterval(pollTimer);
		pollTimer = null;
	}

	onDestroy(teardown);

	async function poll() {
		if (!scope) return;
		try {
			[ra, dec] = await scope.get_position_ra_dec();
			[alt, az] = await scope.get_position_alt_az();
			slewing = await scope.is_slewing();
			if (has('TelescopeTracking')) tracking = await scope.is_tracking();
			if (has('TelescopePark')) parked = await scope.is_parked();
			if (has('TelescopeCover')) coverOpen = await scope.is_cover_open();
			failure = null;
		} catch (error) {
			failure = String(error);
		}
	}

	async function act(label: string, action: () => Promise<unknown>) {
		busy = label;
		failure = null;
		try {
			await action();
			await poll();
		} catch (error) {
			failure = String(error);
		} finally {
			busy = null;
		}
	}

	const fmt = (value: number | null, digits = 4) =>
		value === null ? '—' : value.toFixed(digits);
</script>

<svelte:head><title>chimera — telescope</title></svelte:head>

{#if !telescope}
	<p class="text-sm text-slate-500">
		{connection.status === 'open'
			? 'No telescope registered on this server.'
			: 'Waiting for the gateway connection…'}
	</p>
{:else}
	<div class="mb-6 flex items-center gap-3">
		<h1 class="text-xl font-semibold text-slate-100">Telescope</h1>
		<a href="/object{telescope.path}" class="font-mono text-sm text-sky-300 hover:underline">
			{telescope.path}
		</a>
		{#if slewing}
			<span class="animate-pulse rounded-full bg-amber-500/20 px-2 py-0.5 text-xs text-amber-300">
				slewing
			</span>
		{/if}
		{#if tracking}
			<span class="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-400">
				tracking
			</span>
		{/if}
		{#if parked}
			<span class="rounded-full bg-slate-700 px-2 py-0.5 text-xs text-slate-300">parked</span>
		{/if}
	</div>

	{#if failure}
		<div class="mb-4 rounded border border-red-800 bg-red-950/40 px-3 py-2 text-sm text-red-300">
			{failure}
		</div>
	{/if}

	<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
		{#each [['RA', fmt(ra), 'h'], ['Dec', fmt(dec), '°'], ['Alt', fmt(alt, 2), '°'], ['Az', fmt(az, 2), '°']] as [label, value, unit] (label)}
			<div class="rounded-lg border border-slate-800 bg-slate-900/60 p-4 text-center">
				<div class="text-xs tracking-wide text-slate-500 uppercase">{label}</div>
				<div class="mt-1 font-mono text-2xl text-slate-100">
					{value}<span class="ml-1 text-sm text-slate-500">{unit}</span>
				</div>
			</div>
		{/each}
	</div>

	<div class="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
		<section class="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
			<h2 class="mb-3 text-sm font-medium tracking-wide text-slate-400 uppercase">Slew</h2>
			<form
				class="flex flex-wrap items-end gap-3"
				onsubmit={(e) => {
					e.preventDefault();
					void act('slew', () => scope!.slew_to_ra_dec(Number(targetRa), Number(targetDec)));
				}}
			>
				<label class="flex flex-col gap-1 text-xs text-slate-400">
					<span>RA (hours)</span>
					<input
						type="number"
						step="any"
						required
						bind:value={targetRa}
						class="w-32 rounded border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-200"
					/>
				</label>
				<label class="flex flex-col gap-1 text-xs text-slate-400">
					<span>Dec (degrees)</span>
					<input
						type="number"
						step="any"
						required
						bind:value={targetDec}
						class="w-32 rounded border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-200"
					/>
				</label>
				<button
					type="submit"
					disabled={busy !== null}
					class="rounded bg-sky-600 px-4 py-1.5 text-sm font-medium text-white
					       hover:bg-sky-500 disabled:opacity-50"
				>
					{busy === 'slew' ? 'Slewing…' : 'Slew'}
				</button>
				<button
					type="button"
					onclick={() => void act('abort', () => scope!.abort_slew())}
					class="rounded border border-red-700 px-4 py-1.5 text-sm text-red-300 hover:bg-red-950/40"
				>
					Abort
				</button>
			</form>

			<div class="mt-4 flex flex-wrap gap-2">
				{#if has('TelescopePark')}
					{#if parked}
						<button
							class="rounded border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500"
							disabled={busy !== null}
							onclick={() => void act('unpark', () => scope!.unpark())}
						>
							Unpark
						</button>
					{:else}
						<button
							class="rounded border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500"
							disabled={busy !== null}
							onclick={() => void act('park', () => scope!.park())}
						>
							Park
						</button>
					{/if}
				{/if}
				{#if has('TelescopeTracking')}
					{#if tracking}
						<button
							class="rounded border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500"
							disabled={busy !== null}
							onclick={() => void act('tracking', () => scope!.stop_tracking())}
						>
							Stop tracking
						</button>
					{:else}
						<button
							class="rounded border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500"
							disabled={busy !== null}
							onclick={() => void act('tracking', () => scope!.start_tracking())}
						>
							Start tracking
						</button>
					{/if}
				{/if}
				{#if has('TelescopeCover')}
					<button
						class="rounded border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500"
						disabled={busy !== null}
						onclick={() =>
							void act('cover', () => (coverOpen ? scope!.close_cover() : scope!.open_cover()))}
					>
						{coverOpen ? 'Close cover' : 'Open cover'}
					</button>
				{/if}
			</div>
		</section>

		<section>
			<EventLog entries={log} onclear={() => (log = [])} />
		</section>
	</div>
{/if}
